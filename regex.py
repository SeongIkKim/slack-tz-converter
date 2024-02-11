import re

# time related
# case 1 - 10:30 PM
time_re_pattern = re.compile(r'\s(\d{1,2}\:\d{1,2}\s?(?:AM|PM|am|pm))')

# case 2 ex - 10 PM

date_re_pattern = re.compile(r'\s?(tomorrow|Tomorrow|tmr|Tmr|'
                             r'today|Today|td|Td|'
                             r'yesterday|Yesterday|yd|Yd)\s?')
                             # r'next|'
                             # r'last')