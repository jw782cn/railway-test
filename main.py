from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

@app.get("/calculate/{num1}/{num2}")
async def calculate(num1: float, num2: float):
    """
    计算两个数字的加减乘除结果
    """
    return {
        "addition": num1 + num2,
        "subtraction": num1 - num2,
        "multiplication": num1 * num2,
        "division": num1 / num2 if num2 != 0 else "除数不能为零"
    }