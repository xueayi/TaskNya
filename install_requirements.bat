@echo off
echo ���ڰ�װ������...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo ��װʧ�ܣ����������Ϣ��
) else (
    echo �����������ѳɹ���װ��
)

pause