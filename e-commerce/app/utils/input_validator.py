import re
from fastapi import HTTPException, status

def has_middle_space(input_str):
  return bool(re.search(r'(?<!^)\s(?!$)', input_str))

def check_input_parameter(input_parameter: str)->str:
  if not isinstance(input_parameter,str):
    raise ValueError("Parameter must be a string")
  input_parameter.strip()
  
  if not input_parameter:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=f"Empty {input_parameter}")
  
  if has_middle_space(input_parameter):
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=f"Invalid parameter: {input_parameter}, please enter without empty spaces")
  
  input_parameter = input_parameter.replace(" ", "")
  if not input_parameter:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Empty parameter: {input_parameter}")
  
  return input_parameter

def is_valid_namesurname(input_str):
    regex = r"^[a-zA-Z\s\-&_']+$"
    return bool(re.match(regex, input_str))

def is_valid_username(username: str) -> bool:
    """
    验证用户名：
    - 支持中文、英文、数字
    - 支持下划线 _
    - 不允许特殊字符
    - 长度1-16位
    """
    # 允许中文、英文字母、数字、下划线
    regex = r"^[\u4e00-\u9fa5a-zA-Z0-9_]{1,16}$"
    return bool(re.match(regex, username))

def is_valid_name(name: str) -> bool:
    """
    验证姓名（name/surname）：
    - 支持中文、英文
    - 支持空格、连字符 -、撇号 '
    - 不允许其他特殊字符
    - 长度1-100位
    """
    # 允许中文、英文字母、空格、连字符、撇号
    regex = r"^[\u4e00-\u9fa5a-zA-Z\s\-']{1,100}$"
    return bool(re.match(regex, name))

