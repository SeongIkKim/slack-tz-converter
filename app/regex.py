import re

# time related
# case 1 - 10:30 PM
time_re_pattern = re.compile(r'\s(\d{1,2}(?::\d{2})?\s?(?:AM|PM|am|pm))') # 09:00 PM, 9:00pm, 9 PM, 9 am, etc

# case 2 ex - 10 PM

date_re_pattern = re.compile(r'\b(tomorrow|Tomorrow|tmr|Tmr|'
                             r'today|Today|td|Td|tonight|Tonight|'
                             r'yesterday|Yesterday|yd|Yd|'
                             r'next|Next|'
                             r'last|Last|'
                             r'this|This)\b')

weekday_re_pattern = re.compile(r'\b(monday|Monday|'
                                r'tuesday|Tuesday|'
                                r'wednesday|Wednesday|'
                                r'thursday|Thursday|'
                                r'friday|Friday|'
                                r'saturday|Saturday|'
                                r'sunday|Sunday)\b')