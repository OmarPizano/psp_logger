#!/usr/bin/python3

import time
import sys
from colorama import Fore

FILENAME = "log.txt"

MSG_START = "Started activity ({})"
MSG_INTERRUPT = "Interrupted activity: {} min current delta"
MSG_RESUME = "Resumed activity: {} min interrupted."
MSG_STOP = "Stopped activity ({}): {} min total delta, {} min total interrupted."

class Interruption:
    def __init__(self):
        self.__start_date = 0.0 
        self.__end_date = 0.0
        self.__active = False
    
    def get_start_date(self):
        return self.__start_date

    def get_end_date(self):
        return self.__end_date
        
    def is_active(self):
        return self.__active

    def start(self):
        "Inicia la interrupción."
        if not self.__active:
            self.__start_date = time.time()
            self.__end_date = 0.0
            self.__active = True

    def end(self):
        "Termina la interrupción."
        if self.__active:
            self.__end_date = time.time()
            self.__active = False

    def get_duration(self):
        "Obtiene la duración (secs) de la interrupción."
        if self.__active:
            return False
        return self.__end_date - self.__start_date

class PspActivity:
    def __init__(self):
        self.__start_date = 0.0
        self.__end_date = 0.0
        self.__status = 'not_started' # not_started, active, interrupted, stopped
        self.__interrupted_secs = 0.0
        self.__delta_secs = 0.0
        self.__last_interruption = Interruption()

    def start(self):
        "Registra la fecha de inicio y activa el status."
        self.__start_date = time.time()
        self.__status = 'active'
        return MSG_START.format(self.get_start_date())
    
    def interrupt(self):
        "Agrega una interrupción y actualiza el delta para mostrarlo."
        self.__last_interruption.start()
        self.__delta_secs = (self.__last_interruption.get_start_date() - self.__start_date) - self.__interrupted_secs
        self.__status = 'interrupted'
        return MSG_INTERRUPT.format(self.__sec2min(self.__delta_secs))

    def resume(self):
        "Termina la última interrupción y actualiza el tiempo de interrupción total"
        self.__last_interruption.end()
        self.__interrupted_secs = self.__interrupted_secs + self.__last_interruption.get_duration()
        self.__status = 'active'
        return MSG_RESUME.format(self.__sec2min(self.__last_interruption.get_duration()))

    def stop(self):
        "Obtiene la fecha de terminación y actializa el tiempo delta."
        if self.__status == 'interrupted':
            self.__last_interruption.end()
            self.__interrupted_secs = self.__interrupted_secs + self.__last_interruption.get_duration() 
        self.__end_date = time.time()
        self.__delta_secs = (self.__end_date - self.__start_date) - self.__interrupted_secs
        self.__status = 'stopped'
        return MSG_STOP.format(self.get_end_date(), self.__sec2min(self.__delta_secs), self.__sec2min(self.__interrupted_secs))
    
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

    def get_interrupted_mins(self):
        return self.__sec2min(self.__interrupted_secs)

    def get_delta_mins(self):
        return self.__sec2min(self.__delta_secs)

    def __get_date(self, date_in_secs: float) -> str:
        time_struct = time.localtime(date_in_secs)
        return time.strftime("%Y/%m/%d %H:%M:%S", time_struct)

    def __sec2min(self, secs) -> str:
        minutes, seconds = divmod(secs, 60)
        return round(minutes + seconds/60, 1)

class ActivityLog:
    def __init__(self, program_name: str, phase_name: str, activity: PspActivity, comment: str):
        with open(FILENAME, "a") as logfile:
            logfile.write("{},{},{},{},{},{},{}\n".format(\
                program_name,
                phase_name,
                activity.get_start_date(),
                activity.get_interrupted_mins(),
                activity.get_end_date(),
                activity.get_delta_mins(),
                comment))

class Application:
    def __init__(self):
        self.__program_name = ''
        self.__phase_name = ''
        self.__error_msg = False
        self.__info_msg = False
        self.__options = {'s':'(s)tart', 'i':'(i)nterrupt', 'r':'(r)esume', 't':'s(t)op', 'q': '(q)uit'}

    def run(self):
        activity = PspActivity()
        while True:
            status = activity.get_status()
            valid_options = []
            if status == 'stopped':
                print(self.__gen_prompt(status, self.__info_msg, self.__error_msg, valid_options, True))
                self.__save(activity)
                break
            elif status == 'not_started':
                valid_options.extend(['s', 'q'])
            elif status == 'active':
                valid_options.extend(['i', 't', 'q'])
            elif status == 'interrupted':
                valid_options.extend(['r', 't', 'q']) 
            prompt = self.__gen_prompt(status, self.__info_msg, self.__error_msg, valid_options)
            command = input(prompt)
            self.__error_msg = False # limpiar el error msg luego de generar el prompt
            self.__info_msg = False # limpiar el info msg luego de generar el prompt
            if command in valid_options:
                self.__info_msg = self.__execute_command(command, activity)
            else:
                self.__error_msg = 'Invalid command.'
                continue

    def __save(self, activity: PspActivity):
        comment = input('[?] Write a short comment: ')
        ActivityLog(self.__program_name, self.__phase_name, activity, comment)

    def __execute_command(self, command: str, activity: PspActivity) -> str:
        info = ''
        if command == 's':
            info = activity.start()
        elif command == 'i':
            info = activity.interrupt()
        elif command == 'r':
            info = activity.resume()
        elif command == 't':
            info = activity.stop()
        elif command == 'q':
            exit(0)
        return info

    def __gen_prompt(self, activity_status, info, error, valid_options: list, just_info = False) -> str:
        if activity_status == 'not_started':
            activity_status = Fore.CYAN + activity_status + Fore.RESET
        elif activity_status == 'active':
            activity_status = Fore.GREEN + activity_status + Fore.RESET
        elif activity_status == 'interrupted':
            activity_status = Fore.RED + activity_status + Fore.RESET
        elif activity_status == 'stopped':
            activity_status = Fore.MAGENTA + activity_status + Fore.RESET
        msg = '\n[ {} ]'.format(activity_status)
        if info != False:
            info = Fore.BLUE + info + Fore.RESET
            msg += ' INFO: {}'.format(info)
        if error != False:
            error = Fore.RED + error + Fore.RESET
            if info != False:
                msg += ' |'
            msg += ' ERROR: {}'.format(error)
        if just_info:
            msg += '\n'
            return msg
        msg += '\n{}'.format(self.__gen_command_str(valid_options))
        msg += ' >> '
        return msg

    def __gen_command_str(self, options: list) -> str:
        commands_str = ''
        for o in options:
            commands_str += self.__options[o]
            if options[-1] != o:
                commands_str += ' | '
        return commands_str


    def valid_params(self, params) -> bool:
        if len(params) == 3:
            self.__program_name = params[1]
            self.__phase_name = params[2]
            return True
        else:
            self.__error_msg = '[ ERROR: Invalid parameters. ]'
            return False

    def get_error(self):
        return self.__error_msg

    def get_help(self):
        return 'USAGE:\n\tpython psplogger.py [PROGRAM_NAME] [PHASE_NAME]\nEXAMPLE:\n\tpython psplogger.py PSP0_1 Planning.Step1\n'

# Main Sequence
app = Application()
if app.valid_params(sys.argv):
    app.run()
else:
    print(app.get_error())
    print(app.get_help())