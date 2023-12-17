from fastapi import FastAPI, APIRouter, Request, HTTPException
from pydantic import BaseModel
from hashlib import sha256
import mysql.connector
import qrcode
from fastapi.responses import FileResponse
from datetime import datetime
import os

app = FastAPI(swagger_ui_parameters={"deepLinking": False})
router = APIRouter(prefix="/principal")

mydb = None
try:
    mydb = mysql.connector.connect(
        host='localhost',
        user='Victor',
        password='V1c$or#456',
        database='app_merenda2',
    )
except mysql.connector.Error as err:
    print(f"Erro ao conectar ao banco de dados: {err}")

#gerar o qr code
app.include_router(router)
def generate_qr_code(data: str, file_path: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    img.save(file_path)

#pega o qr code do aluno 
@app.get("/qr_code/{user_id}")
def get_qr_code(user_id: int):
    qr_code_file_path = f"qr_codes/{user_id}_qrcode.png"
    return FileResponse(qr_code_file_path, media_type="image/png", filename=f"qrcode_{user_id}.png")

#função para verificar hora
def verificar_horas():
	hora_atual = datetime.now().strftime('%H')
	return hora_atual
#função para o dia 
def ver_dia():
	dias_da_semana = {
	    'Monday': 'segunda-feira',
	    'Tuesday': 'terça-feira',
	    'Wednesday': 'quarta-feira',
	    'Thursday': 'quinta-feira',
	    'Friday': 'sexta-feira',
	    'Saturday': 'sábado',
	    'Sunday': 'domingo'
	}
	data_e_hora_atual = datetime.now()
	dia_da_semana = data_e_hora_atual.strftime('%A')
	if dia_da_semana in dias_da_semana:
	     return dias_da_semana[dia_da_semana]



@app.get("/home/usuario/autenticar/{id_nome}/{senha}")
def verificar(id_nome, senha):
    if mydb:  
        cursor = mydb.cursor()
        query_usuario = "SELECT nome FROM usuarios WHERE id = %s;"
        cursor.execute(query_usuario, (senha,))
        result = cursor.fetchone()
        if result:
            return {"Bem-vindo"}
        else:
            return {"Usuário não encontrado"}



class Usuario2(BaseModel):
    id_usuario: int
    nome_usuario: str
    senha: str

@app.post("/usuarios/cadastrar")
async def cadastrar(usuario: Usuario2):
    id_usuario = usuario.id_usuario
    nome_usuario = usuario.nome_usuario
    senha = usuario.senha
    if mydb:
        cursor = mydb.cursor()
        query = "SELECT id FROM usuarios where id = %s;"
        cursor.execute(query, (id_usuario,))
        verificar = cursor.fetchone()
        if verificar:
            return {'message': 'Usuário já existe'}
        else:
        
            query = "INSERT INTO usuarios (id, nome,senha) VALUES (%s, %s, %s);"
            cursor.execute(query, (id_usuario, nome_usuario, senha,))
            mydb.commit()
            cursor.close()
            return {'message': 'Cadastrado com sucesso'}
    else:
        return {'message': 'Você não está autorizado a cadastrar um novo usuário.'}

#parte dos alunos 
class Aluno(BaseModel):
    matricula: int
    nomes: str
@app.post("/alunos/cadastrar")
async def cadastrar(aluno: Aluno):
    matricula = aluno.matricula
    nome = aluno.nomes
    if mydb:
        cursor = mydb.cursor()
        qr_code_data = f"{matricula}"
        query = "INSERT INTO alunos_info (matricula,nome) VALUES (%s, %s)"
        cursor.execute(query, (matricula, nome,))
        mydb.commit()
        qr_code_file_path = f"qr_codes/{matricula}_qrcode.png"
        generate_qr_code(qr_code_data, qr_code_file_path)
        return {'message': "aluno criado" 'QR Code criado com sucesso', 'qr_code_path': qr_code_file_path}

@app.get("/home/autenticar/{aluno_id}")
def verificar(aluno_id):
    if mydb:
        cursor = mydb.cursor()
        query = "SELECT nome FROM alunos_info WHERE matricula = %s;"
        cursor.execute(query, (aluno_id,))
        nome = cursor.fetchone()
        if nome:
            apenas_hora = "0"
            hora_completa = verificar_horas()
            for i in range(2):
                apenas_hora += str(int(hora_completa.split(':')[i]))
                query_turno = "SELECT t.horas FROM turnos t JOIN alunos_tem_turnos att ON t.id = att.id_turno JOIN alunos_info as ai ON ai.matricula = att.id_alunos WHERE HOUR(t.horas) = %s AND ai.matricula = %s;"
                cursor.execute(query_turno, (apenas_hora, aluno_id,))
                turno_valido = cursor.fetchone()
                if turno_valido:
                    hoje = ver_dia()
                    query_disciplina = "SELECT d.nome FROM disciplinas d JOIN alunos_info JOIN alunos_tem_disciplinas atd ON atd.id_alunos = %s AND d.id = atd.id_disciplinas JOIN disciplinas_tem_dias_tem_turnos dtt ON d.id = dtt.id_disciplinas JOIN dias di ON di.id = dtt.id_dias JOIN turnos t ON t.id = dtt.id_turno WHERE di.nome = %s AND HOUR(t.horas) = %s AND alunos_info.matricula = atd.id_alunos;"
                    cursor.execute(query_disciplina, (aluno_id, hoje, apenas_hora,))
                    disciplina_valida = cursor.fetchone()
                    if disciplina_valida:
                        query_merenda = "SELECT aluno_merendou FROM alunos_info WHERE matricula = %s;"
                        cursor.execute(query_merenda, (aluno_id,))
                        merendou = cursor.fetchone()
                        if merendou == 0:
                            return {"pelo que eu sei, já pode ao menos tentar merendar"}
                        else:
                            return {"aluno já merendou, liberar mesmo assim?"}
                    else:
                        return {"mensagem": "aluno sem matrícula neste turno, liberar mesmo assim?"}
                else:
                    return {"mensagem": "aluno sem turno correspondente, liberar mesmo assim?"}
        else:
            return {"cadastro não encontrado"}
    else:
        return {"Não foi possível se conectar ao banco de dados ;("}

class Controle(BaseModel):
    id: int

@app.post("/home/registrar_merenda")
async def aluno_merendou(controle: Controle):
    id = controle.id
    query = "UPDATE alunos_info SET aluno_merendou = 1 WHERE matricula = %s;" 
    if mydb:
        try:
            cursor = mydb.cursor()
            cursor.execute(query, (id,))
            mydb.commit()
            cursor.close()
            return {"mensagem": "ja pode ao mostrar"}
        except Exception as e:
            return HTTPException(403, detail={"mensagem": f"Erro ao registrar merenda: {e}"})
    else:
        return {"mensagem": "Não foi possível se conectar ao banco de dados"}



def verificar_data():
	data = datetime.now().strftime("%Y-%m-%d")
	return data
#autorização especial
class Autorizacao(BaseModel):
    id_aluno: str
    id_usuario: str
    id_turno: str
    motivo: str
    data: str

@app.post("/home/registrar_merenda_autorizacao")
async def autorizar_aluno(autorizacao: Autorizacao):
    query = "INSERT INTO autorização_especial (id_aluno, id_usuario, id_turno, motivo, data) VALUES (%s, %s, %s, %s, %s);"
    cursor = mydb.cursor()
    cursor.execute(query, (autorizacao.id_aluno, autorizacao.id_usuario, autorizacao.id_turno, autorizacao.motivo, autorizacao.data))
    mydb.commit()
    cursor.close()
    return {"mensagem": "autorização concedida, já pode ao mostrar"}