import logging
import re
import colorama

colorama.init(autoreset=True)


class CuteColorFormatter(logging.Formatter):
    """
    Cute & Colorful Formatter for Django Server Logs 🌸✨
    """

    PINK = "\033[38;5;213m"
    CYAN = "\033[38;5;117m"
    GREEN = "\033[38;5;120m"
    YELLOW = "\033[38;5;221m"
    RED = "\033[38;5;204m"
    PURPLE = "\033[38;5;141m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    def format(self, record):
        msg = super().format(record)

        method_map = {
            "GET": f"{self.CYAN}{self.BOLD}GET{self.RESET}",
            "POST": f"{self.PINK}{self.BOLD}🚀 POST{self.RESET}",
            "PUT": f"{self.YELLOW}{self.BOLD}⚡ PUT{self.RESET}",
            "PATCH": f"{self.PURPLE}{self.BOLD}🛠️ PATCH{self.RESET}",
            "DELETE": f"{self.RED}{self.BOLD}🗑️ DELETE{self.RESET}",
            "OPTIONS": f"{self.DIM}🔍 OPTIONS{self.RESET}",
        }

        # Match HTTP server request lines: "GET /path/ HTTP/1.1" 200 1234
        match = re.search(
            r'"(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+([^\s]+)\s+HTTP/[^"]+"\s+(\d{3})\s+(\d+|-)',
            msg,
        )
        if match:
            method, path, status_code, size = match.groups()
            status_int = int(status_code)

            if 200 <= status_int < 300:
                if status_int == 201:
                    status_str = (
                        f"{self.GREEN}{self.BOLD}🎉 {status_code} CREATED{self.RESET}"
                    )
                else:
                    status_str = (
                        f"{self.GREEN}{self.BOLD}🟢 {status_code} OK ✨{self.RESET}"
                    )
            elif 300 <= status_int < 400:
                status_str = (
                    f"{self.CYAN}{self.BOLD}🔀 {status_code} REDIRECT{self.RESET}"
                )
            elif 400 <= status_int < 500:
                if status_int == 404:
                    status_str = f"{self.YELLOW}{self.BOLD}🔍 {status_code} NOT FOUND 🙈{self.RESET}"
                elif status_int in (401, 403):
                    status_str = f"{self.YELLOW}{self.BOLD}🔒 {status_code} FORBIDDEN 🛑{self.RESET}"
                else:
                    status_str = f"{self.YELLOW}{self.BOLD}⚠️ {status_code} BAD REQUEST{self.RESET}"
            else:
                status_str = f"{self.RED}{self.BOLD}💥 {status_code} SERVER ERROR 😿{self.RESET}"

            method_str = method_map.get(method, f"{self.BOLD}{method}{self.RESET}")
            path_str = f"{self.PINK}{path}{self.RESET}"
            time_str = f"{self.DIM}[{self.formatTime(record, '%H:%M:%S')}]{self.RESET}"

            return f" {time_str} {method_str} {path_str} ➔ {status_str}"

        # Non-HTTP general log messages
        if record.levelno >= logging.ERROR:
            return f"💥 {self.RED}{self.BOLD}[ERROR]{self.RESET} {record.getMessage()} 😿"
        elif record.levelno >= logging.WARNING:
            return f"⚠️ {self.YELLOW}{self.BOLD}[WARN]{self.RESET} {record.getMessage()} 🐥"
        elif record.levelno >= logging.INFO:
            return f"✨ {self.CYAN}[INFO]{self.RESET} {record.getMessage()} 💖"

        return f"🌸 {msg}"
