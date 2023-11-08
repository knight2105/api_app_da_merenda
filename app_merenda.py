from fastapi import FastAPI, APIRouter
import uvicorn
import mysql.connector
from hashlib import sha256

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

app = FastAPI()

app.include_router(router)

@router.post("/cadastrar_usuario/")
def cadastrar_usuario(id_usuario: int, nome_usuario: str, tipo: int, senha: str):
    if mydb:
        cursor = mydb.cursor()
        query = "SELECT id FROM usuarios where id = %s;"
        cursor.execute(query, (id_usuario,))
        verificar = cursor.fetchone()
        if verificar:
            return {'message': 'Usuário já existe'}
        else:
            crip_senha = sha256(senha.encode()).hexdigest()
            cursor = mydb.cursor()
            query = "INSERT INTO usuarios (id, nome, tipo, senha) VALUES (%s, %s, %s, %s);"
            cursor.execute(query, (id_usuario, nome_usuario, tipo, crip_senha,))
            mydb.commit()
            cursor.close()
            return {'message': 'Cadastrado com sucesso'}
    else:
        return { 'message': 'Você não está autorizado a cadastrar um novo usuário.' }

@router.get("/buscar_aluno/")
def buscar_aluno(matricula: int):
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000 )
