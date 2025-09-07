import psutil
import requests
import time
from datetime import datetime
import json

SERVER_URL = "http://192.168.хх.хх:хххх/report" # настройка хоста

# хранение информации о текущих процессах
active_processes_info = {}
closed_processes_info = {}

def get_active_processes():
    # захват списка всех активных процессов
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        processes.append(proc.info)
    return processes

def check_new_and_closed_processes(current_processes):
    global active_processes_info, closed_processes_info
    new_processes = []
    closed_processes = []

    # проверка на новые процессы
    for proc in current_processes:
        pid = proc['pid']
        if pid not in active_processes_info:
            new_processes.append({
                'name': proc['name'],
                'pid': pid
            })
            active_processes_info[pid] = {
                'name': proc['name']
            }

    # проверка на закрытые процессы
    for pid in list(active_processes_info.keys()):
        if pid not in [proc['pid'] for proc in current_processes]:
            closed_processes.append({
                'name': active_processes_info[pid]['name'],
                'pid': pid
            })
            closed_processes_info[pid] = {
                'name': active_processes_info[pid]['name']
            }
            del active_processes_info[pid]  # удаление закрытого из активных процессов

    if new_processes:
        new_processes = json.dumps(new_processes, indent=4)
    if closed_processes:
        closed_processes = json.dumps(closed_processes, indent=4)

    return new_processes, closed_processes

def send_report(new_processes, closed_processes):
    # отправка отчетов о новых и закрытых процессах
    report = {}
    if new_processes:
        report['new_processes'] = new_processes
    if closed_processes:
        report['closed_processes'] = closed_processes

    if report:
        try:
            response = requests.post(SERVER_URL, json=report)
            if response.status_code == 200:
                print(">>> Данные успешно отправлены на сервер.\n>>> Время проверки:", format_time(datetime.now()), "\n")
            else:
                print(f"Ошибка при отправке данных: {response.status_code}, ответ: {response.text}")
        except Exception as e:
            print(f"Не удалось отправить данные: {e}")

def format_time(timestamp):
    return timestamp.strftime("%H:%M:%S")  # формат времени в нормальный вид в hh:mm:ss

def main():
    while True:
        active_processes = get_active_processes()
        new_processes, closed_processes = check_new_and_closed_processes(active_processes)

        if new_processes:
            print(f"Новые процессы:\n{new_processes}")

        if closed_processes:
            print(f"Закрытые процессы:\n{closed_processes}")

        if not new_processes and not closed_processes:
            print("[ INFO ] Нет закрытых или открытых процессов\n"
                  "Время проверки:", format_time(datetime.now()))
        elif new_processes and not closed_processes:
            print("[ INFO ] Нет закрытых процессов\n"
                  "Время проверки:", format_time(datetime.now()))
        elif not new_processes and closed_processes:
            print("[ INFO ] Нет открытых процессов\n"
                  "Время проверки:", format_time(datetime.now()))


        send_report(new_processes, closed_processes)

        time.sleep(10)

if __name__ == "__main__":
    main()
