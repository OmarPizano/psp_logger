#!/usr/bin/python3

import time
import sys
from colorama import Fore

class Interruption:
    """
    Esta clase se usa para generar una interrupción.
    """
    def __init__(self):
        """
        Inicializa las fechas (inicio y fin) de la interrupción a 0.0 y
        pone el estado en False.
        """
        self.__start_date = 0.0 
        self.__end_date = 0.0
        self.__active = False
    
    def get_start_date(self) -> float:
        "Retorna la fecha (segundos desde EPOCH) de inicio de la interrupción."
        return self.__start_date

    def get_end_date(self) -> float:
        "Retorna la fecha (segundos desde EPOCH) de finalización de la interrupción."
        return self.__end_date
        
    def is_active(self) -> bool:
        "Retorna el estado de la interrupción (true/false)."
        return self.__active

    def start(self):
        """
        Inicia la interrupción tomando la fecha actual como la fecha de inicio.
        Si la interrupción ya estaba activa, no hace nada.
        """
        if not self.__active:
            self.__start_date = time.time()
            self.__end_date = 0.0
            self.__active = True

    def end(self):
        """
        Termina la interrupción tomando la fecha actual como la fecha de finalización.
        Si la interrupción no estaba activa, no hace nada.
        """
        if self.__active:
            self.__end_date = time.time()
            self.__active = False

    def get_duration(self):
        """
        Retorna la duración total de la interrupción restando las fechas de inicio
        y fin.
        Si la interrupción sigue activa, retorna False.
        """
        if self.__active:
            return False
        return self.__end_date - self.__start_date

class PspStep:
    """
    Esta clase representa un step de una fase de cierto script del PSP.

    Los posibles estados son: 'not_started', 'active', 'interrupted' y 'stopped.
    """
    INFO = {
        "start": "Started step ({})",
        "interrupt": "Interrupted step: {} min current delta",
        "resume": "Resumed step: {} min interrupted.",
        "stop": "Stopped step ({}): {} min total delta, {} min total interrupted."
    }
    def __init__(self):
        """
        Inicializa el step.
        El estado se pone en 'not_started'
        """
        self.__start_date = 0.0
        self.__end_date = 0.0
        self.__status = 'not_started' # not_started, active, interrupted, stopped
        self.__interrupted_secs = 0.0
        self.__delta_secs = 0.0
        self.__last_interruption = Interruption()

    def start(self):
        """
        Establece la fecha de inicio del step y el estado 'active'.
        
        Retorna información de la fecha de inicio.
        """
        self.__start_date = time.time()
        self.__status = 'active'
        return self.INFO['start'].format(self.get_start_date())
    
    def interrupt(self):
        """
        Inicia la interrupción del step y pone el estado a 'interrupted'.

        Retorna información del tiempo total delta transcurrido hasta la interrupción.
        """
        self.__last_interruption.start()
        self.__delta_secs = (self.__last_interruption.get_start_date() - self.__start_date) - self.__interrupted_secs
        self.__status = 'interrupted'
        return self.INFO['interrupt'].format(self.__sec2min(self.__delta_secs))

    def resume(self):
        """
        Termina la interrupción del step y suma su duración al tiempo de interrupción total.
        Pone el estado a 'active'.

        Retorna información sobre el tiempo que duró la interrupción.
        """
        self.__last_interruption.end()
        self.__interrupted_secs = self.__interrupted_secs + self.__last_interruption.get_duration()
        self.__status = 'active'
        return self.INFO['resume'].format(self.__sec2min(self.__last_interruption.get_duration()))

    def stop(self):
        """
        Establece la fecha de finalización del step y actualiza el tiempo total delta.
        Para ello resta la interrupción total al tiempo transcurrido entre la fecha de inicio
        y la fecha de finalización. Pone el estado a 'stopped'.

        Retorna información sobre el delta total, interrupción total y la fecha de finalización.
        """
        if self.__status == 'interrupted':
            self.__last_interruption.end()
            self.__interrupted_secs = self.__interrupted_secs + self.__last_interruption.get_duration() 
        self.__end_date = time.time()
        self.__delta_secs = (self.__end_date - self.__start_date) - self.__interrupted_secs
        self.__status = 'stopped'
        return self.INFO['stop'].format(self.get_end_date(), self.__sec2min(self.__delta_secs), self.__sec2min(self.__interrupted_secs))
    
    def get_status(self):
        """
        Regresa alguno de los posibles estados:
        - not_started
        - active
        - interrupted
        - stopped
        """
        return self.__status

    def get_start_date(self):
        """
        Retorna la fecha de inicio del step en formato YYYY/MM/DD_HH:MM:SS.

        Si el step no ha sido iniciado, retorna False
        """
        if self.__status == 'not_started':
            return False
        return self.__get_date(self.__start_date)
    
    def get_end_date(self):
        """
        Retorna la fecha de finalización del step en formato YYYY/MM/DD_HH:MM:SS.

        Si el step no ha sido detenido, retorna False
        """
        if self.__status != 'stopped':
            return False
        return self.__get_date(self.__end_date)

    def get_interrupted_mins(self):
        """
        Retorna el tiempo total de interrupción en minutos.

        Se aplica un redondeo a 1 decimal.
        """
        return self.__sec2min(self.__interrupted_secs)

    def get_delta_mins(self):
        """
        Retorna el tiempo total delta en minutos.
        
        Se aplica un redondeo a 1 decimal.
        """
        return self.__sec2min(self.__delta_secs)

    def __get_date(self, date_in_secs: float) -> str:
        """
        Convierte la fecha en segundos a una fecha en formato string YYYY/MM/DD_HH:MM:SS.
        """
        time_struct = time.localtime(date_in_secs)
        return time.strftime("%Y/%m/%d_%H:%M:%S", time_struct)

    def __sec2min(self, secs) -> str:
        """
        Convierte los segundos a minutos aplicando un redondeo de 1 decimal.
        """
        minutes, seconds = divmod(secs, 60)
        return round(minutes + seconds/60, 1)

class StepLog:
    """
    Esta clase representa el archivo donde se va a registrar cada step.
    """
    def __init__(self, program_name: str, phase_name: str, step: PspStep, comment: str):
        """
        Inicializa el objeto con el nombre el programa, la fase y los datos de una actividad terminada.
        """
        self.__log = "{}, {}, {}, {}, {}, {}, {}\n".format(\
                program_name,
                phase_name,
                step.get_start_date(),
                step.get_interrupted_mins(),
                step.get_end_date(),
                step.get_delta_mins(),
                comment)
    
    def write(self, filename: str):
        """
        Agrega los datos del step en el archivo de registro indicado.
        Si el archivo no existe, lo crea.
        """
        log = Fore.YELLOW + self.__log + Fore.RESET
        print("\nNew log: {}".format(log))
        with open(filename, "a") as logfile:
            logfile.write(self.__log)

class Application:
    def __init__(self):
        self.__file_name = ''
        self.__program_name = ''
        self.__phase_name = ''
        self.__error_msg = False
        self.__info_msg = False
        self.__options = {'s':'(s)tart', 'i':'(i)nterrupt', 'r':'(r)esume', 't':'s(t)op', 'q': '(q)uit'}

    def run(self):
        step = PspStep()
        while True:
            status = step.get_status()
            valid_options = []
            if status == 'stopped':
                print(self.__gen_prompt(status, self.__info_msg, self.__error_msg, valid_options, True))
                self.__save(step)
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
                self.__info_msg = self.__execute_command(command, step)
            else:
                self.__error_msg = 'Invalid command.'
                continue

    def __save(self, step: PspStep):
        comment = self.__parse_comment(input('[?] Step comment: '))
        log = StepLog(self.__program_name, self.__phase_name, step, comment)
        log.write(self.__file_name)
        
    def __parse_comment(self, comment: str) -> str:
        comment = comment[0:50]
        comment = comment.replace(',','')
        return comment

    def __execute_command(self, command: str, step: PspStep) -> str:
        info = ''
        if command == 's':
            info = step.start()
        elif command == 'i':
            info = step.interrupt()
        elif command == 'r':
            info = step.resume()
        elif command == 't':
            info = step.stop()
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
        if len(params) == 4:
            self.__file_name = params[1]
            self.__program_name = params[2]
            self.__phase_name = params[3]
            return True
        else:
            self.__error_msg = '[ ERROR: Invalid parameters. ]'
            return False

    def get_error(self):
        return self.__error_msg

    def get_help(self):
        return 'USAGE:\n\tpython psplogger.py [LOG_FILE] [PROGRAM_NAME] [PHASE_NAME]\nEXAMPLE:\n\tpython psplogger.py PSP0_1 Planning.Step1\n'

# Main Sequence
app = Application()
if app.valid_params(sys.argv):
    app.run()
else:
    print(app.get_error())
    print(app.get_help())