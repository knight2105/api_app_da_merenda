from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from hashlib import sha256
import mysql.connector
import qrcode
from fastapi.responses import FileResponse
import os

class Aluno(BaseModel):
    matricula: int
    nomes: str
    id_curso: int


app = FastAPI(swagger_ui_parameters={"deepLinking": False})
router = APIRouter(prefix="/principal")

mydb = None
try:
    mydb = mysql.connector.connect(
        host='localhost',
        user='Victor',
        password='V1c$or#456',
        database='app_merenda',
    )
except mysql.connector.Error as err:
    print(f"Erro ao conectar ao banco de dados: {err}")

app.include_router(router)

# Função para gerar um QR Code e salvar em um arquivo
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

    # Certifica-se de que o diretório existe antes de salvar
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    img.save(file_path)

@app.post("/alunos/cadastrar")
async def cadastrar_aluno(aluno: Aluno):
    print(aluno)
    matricula = aluno.matricula
    nomes = aluno.nomes
    id_curso = aluno.id_curso

    if mydb:
        cursor = mydb.cursor()

        # Verifica se a matrícula já existe
        query = "SELECT matricula FROM alunos_info where matricula = %s;"
        cursor.execute(query, (matricula,))
        verificar = cursor.fetchone()

        if verificar:
            return {'message': 'Aluno já cadastrado'}
        else:
            # Adiciona o gerador de QR Code
            qr_code_data = f"Matrícula: {matricula}\nNomes: {nomes}\nCurso: {id_curso}"
            qr_code_file_path = f"qr_codes/{matricula}_qrcode.png"
            generate_qr_code(qr_code_data, qr_code_file_path)

            # Insere os dados do aluno no banco de dados
            query = "INSERT INTO alunos_info (matricula, nomes, QR, id_curso) VALUES (%s, %s, %s, %s);"
            cursor.execute(query, (matricula, nomes, qr_code_file_path,id_curso))
            mydb.commit()
            cursor.close()

            return {'message': 'Aluno cadastrado com sucesso', 'qr_code_path': qr_code_file_path}
    else:
        return {'message': 'Você não está autorizado a cadastrar um novo aluno.'}


@app.get("/buscar_aluno/{matricula}")
def get_buscar_aluno(matricula: int):
    if mydb:
        cursor = mydb.cursor()

       
        query = "SELECT * FROM alunos_info where matricula = %s;"
        cursor.execute(query, (matricula,))
        dados_aluno = cursor.fetchone()
        cursor.close()

        if dados_aluno:
            return {"informacoes": dados_aluno}
        else:
            return {"message": "Aluno não encontrado"}
    else:
        return {"message": "Você está offline ;("}

@app.get("/qr_code/{matricula}")
def get_qr_code(matricula: int):
    qr_code_file_path = f"qr_codes/{matricula}_qrcode.png"
    return FileResponse(qr_code_file_path, media_type="image/png", filename=f"qrcode_{matricula}.png")
