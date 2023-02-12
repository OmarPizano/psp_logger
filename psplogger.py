#!/usr/bin/python3

import time

FILENAME = "log.txt"

MSG_START = "Started activity ({})"
MSG_INTERRUPT = "Interrupted activity: {} min current delta"
MSG_RESUME = "Resumed activity: {} min interrupted."
MSG_STOP = "Stopped activity ({}): {} min total delta, {} min total interrupted."

class Interruption:
    def __init__(self):
        self.__start_date = time.time()
        self.__end_date = None
        self.__active = True
    
    def get_start_date(self):
        return self.__start_date

    def get_end_date(self):
        return self.__end_date
        
    def is_active(self):
        return self.__active

    def end(self):
        "Termina la interrupción."
        if self.__active:
            self.__end_date = time.time()
            self.__active = False

    def get_duration_min(self):
        "Obtiene la duración de la interrupción en minutos."
        if self.__active:
            return False
        return int(divmod(self.__end_date - self.__start_date, 60)[0])

class PspActivity:
    def __init__(self):
        self.__start_date = 0.0
        self.__end_date = 0.0
        self.__status = 'not_started' # not_started, active, interrupted, stopped
        self.__interrupted_min = 0
        self.__delta_min = 0
        self.__interruptions = []

    def start(self):
        "Registra la fecha de inicio y activa el status."
        self.__start_date = time.time()
        self.__status = 'active'
        return MSG_START.format(self.get_start_date())
    
    def interrupt(self):
        "Agrega una interrupción y actualiza el delta para mostrarlo."
        self.__interruptions.append(Interruption())
        self.__delta_min = int(divmod(self.__interruptions[-1].get_start_date() - self.__start_date, 60)[0] - self.__interrupted_min)
        self.__status = 'interrupted'
        return MSG_INTERRUPT.format(self.__delta_min)

    def resume(self):
        "Termina la última interrupción y actualiza el tiempo de interrupción total"
        self.__interruptions[-1].end()
        self.__interrupted_min = self.__interrupted_min + self.__interruptions[-1].get_duration_min()
        self.__status = 'active'
        return MSG_RESUME.format(self.__interruptions[-1].get_duration_min())

    def stop(self):
        "Obtiene la fecha de terminación y actializa el tiempo delta."
        self.__end_date = time.time()
        self.__delta_time = int(divmod(self.__end_date - self.__start_date, 60)[0] - self.__interrupted_min)
        self.__status = 'stopped'
        return MSG_STOP.format(self.get_end_date(), self.__delta_min, self.__interrupted_min)
    
    def get_status(self):
        "not_started, active, interrupted, stopped"
        return self.__status

    def get_start_date(self):
        "Retorna la fecha de inicio formateada."
        if self.__status == 'not_started':
            return False
        return self.__get_date(self.__start_date)
    
    def get_end_date(self):
        "Retorna la fecha de terminación formateada."
        if self.__status != 'stopped':
            return False
        return self.__get_date(self.__end_date)

    def get_interrupt_time(self):
        return self.__interrupted_min

    def get_delta_time(self):
        return self.__delta_min

    def __get_date(self, date_in_secs: float) -> str:
        time_struct = time.localtime(date_in_secs)
        return time.strftime("%Y/%m/%d %H:%M", time_struct)

class ActivityLog:
    def __init__(self, program_name: str, phase_name: str, activity: PspActivity, comment: str):
        with open(FILENAME, "w") as logfile:
            logfile.write("{},{},{},{},{},{},{}\n".format(\
                program_name,
                phase_name,
                activity.get_start_date(),
                activity.get_interrupt_time(),
                activity.get_end_date(),
                activity.get_delta_time(),
                comment))

# TODO: implement main sequence