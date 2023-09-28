import time
from pyModbusTCP.client import ModbusClient
import pandas as pd
#import matplotlib.pyplot as plt
import mysql.connector
import datetime

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="pinguin",
  database="tlk33"
)
mycursor = mydb.cursor()
#mycursor.execute("CREATE TABLE 1stTLK33 (id INT AUTO_INCREMENT PRIMARY KEY, temperature FLOAT, powerHeat FLOAT, powerCool FLOAT, Kp FLOAT, Ki FLOAT, Kd FLOAT, Tcr1 FLOAT, Tcr2 FLOAT, time TIMESTAMP)")
# Инициализация #DEFAULT HOST = 192.168.1.99
c = ModbusClient(host='10.90.90.231', port=502, unit_id=2, debug=False, auto_open=True)

data_SP = ["SP1", "SP2", "SP3", "SP4"]
nSP = str(c.read_holding_registers(int('0x2800', 16)))
current_SP = data_SP[int(nSP[1:-1] + nSP[-1:1]) - 1]
match current_SP: # match-case для отображения текущей точки со значением стабилизации
     case "SP1":
            SP1 = str(c.read_holding_registers(int('0x2802', 16)))
            splittedPoint1 = SP1[1:-2]+'.'+SP1[-2]
            print('Точка стабилизации на втором %s:' % current_SP, splittedPoint1, '°C')
     case "SP2":
            SP2 = str(c.read_holding_registers(int('0x2802', 16)))
            splittedPoint2 = SP2[1:-2] + '.' + SP2[-2]
            print('Точка стабилизации на втором %s:' % current_SP, splittedPoint2, '°C')
     case "SP3":
            SP3 = str(c.read_holding_registers(int('0x2802', 16)))
            splittedPoint3 = SP3[1:-2] + '.' + SP3[-2]
            print('Точка стабилизации на втором %s:' % current_SP, splittedPoint3, '°C')
     case "SP4":
            SP4 = str(c.read_holding_registers(int('0x2802', 16)))
            splittedPoint4 = SP4[1:-2] + '.' + SP4[-2]
            print('Точка стабилизации на втором %s:' % current_SP, splittedPoint4, '°C')
data_sensor = ["J","CrAL","S","Ir.J","Ir.Ca","PTC","NTC","0.50mV","0.60mV","12.60mV"]
current_sensor = c.read_holding_registers(int('0x2809', 16))
print('Текущий тип датчика на втором:', data_sensor[int(current_sensor[0])])

database = []
timebase = []
powerbase = []
powerbasecool = []

while True:
    try:

        # Блок температуры и мощности
        measuredTempValue = str(c.read_holding_registers(int('0x200', 16)))
        measuredHeatPowerValue = str(c.read_holding_registers(int('0x203', 16)))
        measuredCoolPowerValue = str(c.read_holding_registers(int('0x204', 16)))
        proportion = str(c.read_holding_registers(int('0x283B', 16)))
        integral = str(c.read_holding_registers(int('0x283C', 16)))
        differ = str(c.read_holding_registers(int('0x283D', 16)))


        # Блок отлавливания ошибок, связанных с неправильными условиями
        measuredValueError = measuredTempValue[1:-1]
        match measuredValueError:
            # При возникновении ошибки с границами, регистр с dP обнуляется, поэтому необходимо
            # повторное присваивания dP одного знака после запятой, так как все алгоритмы срезов и форматированного
            # вывода работают при условии dP = 1
            case '-10000':
                print('Полученные значения меньше заданных диапазонов. '
                      'Проверьте соединение между датчиком и контроллером.')
                c.write_single_register(int('0x280C',16), 1)
                c.write_single_register(int('0x39B',16), 0)
                time.sleep(1)
                break
            case '10000':
                print('Полученные значения больше заданных диапазонов. '
                      'Проверьте соединение между датчиком и контроллером.')
                c.write_single_register(int('0x280C', 16), 1)
                c.write_single_register(int('0x39B', 16), 0)
                time.sleep(1)
                break
            case '10001':
                print('Переполнение при A/D')
                c.write_single_register(int('0x280C', 16), 1)
                c.write_single_register(int('0x39B', 16), 0)
                time.sleep(1)
                break
            case '10003':
                print('Данные недоступны')
                c.write_single_register(int('0x280C', 16), 1)
                c.write_single_register(int('0x39B', 16), 0)
                time.sleep(1)
                break
        # Блок проверки регистров на наличие пустых значений. Необходимо для отправки устройства в сон при активации
        # ручного режима конфигурации (кнопками).
        checkNone = any([measuredTempValue == "None", measuredHeatPowerValue == "None", measuredCoolPowerValue == "None",
                  proportion == "None", integral == "None", differ == "None"])
        if checkNone == True:
                print('Обнаружен пустой регистр. Возможен скоростной сбой')
                print('Контроллер находится в режиме переконфигурирования, ожидание...')
                time.sleep(2)
                continue
        # Состояние регулятора: 0 = off, 1 = auto, 2 = tuning, 3 = man (ручное).
        data_status = ["OFF", "AUTO", "TUNING", "MAN"]
        current_status = str(c.read_holding_registers(int('0x20F',16)))
        print('Первый TLK33')
        print('Мощность на выходе HEAT:', measuredHeatPowerValue[1:-3] + '.' + measuredHeatPowerValue[-2:-1],'%')
        print('Мощность на выходе COOL:', measuredCoolPowerValue[1:-3] + '.' + measuredCoolPowerValue[-2:-1],'%')

        # проверка состояние регулятора знаков после запятой
        dP_status = str(c.read_holding_registers(int('0x280C', 16)))
        if ((dP_status[1:-1] + dP_status[-1:1]) == '1'):
                    print('Значение температуры:', measuredTempValue[1:-2]+'.'+measuredTempValue[-2], '°C')
        else:
            print('Значение температуры:', measuredTempValue[1:-1], '°C')
        print()
        print('ПИД-регулятор')
        print('Текущее состояние ПИД-регулятора:', data_status[int(current_status[1])])
        # проверка состояния режима
        mode_status = str(c.read_holding_registers(int('0x2838', 16)))
        if (data_status[int(current_status[1])] == 'AUTO'):
            print('Выбранный режим AUTO регуляции:', mode_status[1:-1] + mode_status[-1:1])
        if (data_status[int(current_status[1])] == 'OFF'):
            print('ПИД-регулятор в режиме OFF')
            time.sleep(1)
            break
        # Настройка выхода на плато
        Slor = str(c.read_holding_registers(int('0x2844', 16)))
        Slof = str(c.read_holding_registers(int('0x2846', 16)))
        print('Градиент нарастающего фронта (Slor):', Slor[1:-2] + '.' + Slor[-2:-1])
        print('Градиент спадающего фронта (Slof):', Slof[1:-2] + '.' + Slof[-2:-1])

        dtbT = measuredTempValue[1:-2] + '.' + measuredTempValue[-2]
        dtpH = measuredHeatPowerValue[1:-3] + '.' + measuredHeatPowerValue[-2:-1]
        dtpC = measuredCoolPowerValue[1:-3] + '.' + measuredCoolPowerValue[-2:-1]
        dtKp = proportion[1:-2] + '.' + proportion[2]
        dtKi = integral[1:-1] + integral[-1:1]
        dtKd = differ[1:-1] + differ[-1:1]
        tcr1 = str(c.read_holding_registers(int('0x283F', 16)))
        tcr2 = str(c.read_holding_registers(int('0x2841', 16)))
        # ПИД-регулятор, значения
        print('Пропорциональная составляющая:', dtKp)
        print('Интегрирующая составляющая:', dtKi)
        print('Дифференцирующая составляющая:', dtKd)

        with open('datawithkoef1.csv', 'a') as f:
            # записываем данные в файл
            temperature = dtbT
            # timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp = datetime.datetime.utcnow()
            powerHeat = dtpH
            powerCool = dtpC
            Kp = dtKp
            Ki = dtKi
            Kd = dtKd

            frmtdTcr1 = tcr1[1:-1] + tcr1[-1:1]
            frmtdTcr2 = tcr2[1:-1] + tcr2[-1:1]
            dtTcr1 = frmtdTcr1
            dtTcr2 = frmtdTcr2
            row = f'{temperature},{timestamp},{powerHeat},{powerCool},{Kp},{Ki},{Kd}, {dtTcr1}, {dtTcr2}\n'
            f.write(row)

            # вставляем данные в таблицу


            sql2 = "INSERT INTO 1stTLK33 (temperature, time, powerHeat, powerCool, Kp, Ki, Kd) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            val2 = (temperature, timestamp, powerHeat, powerCool, Kp, Ki, Kd)
            mycursor.execute(sql2, val2)
            # сохраняем изменения
            mydb.commit()
        time.sleep(1)
    except KeyboardInterrupt:
        print()
        print('Программа прерывается оператором, завершение работы...')
        time.sleep(1)
        break
    except ValueError:
        print()
        print('Ошибка считывания полученного пакета данных')
        continue
    except mysql.connector.Error as err:
        print("Ошибка при выполнении SQL-запроса: {}".format(err))
        continue

