import re

# time related
# case 1 - 10:30 PM
time_re_pattern = re.compile(r'\s(\d{1,2}\:\d{1,2}\s?(?:AM|PM|am|pm))')

# case 2 ex - 10 PM


# date related

# timezone related
timezone_re_pattern = re.compile(r'pst|PST|pdt|PDT|est|EST|edt|EDT|cst|CST|cdt|CDT|utc|UTC|gmt|GMT|kst|KST|jst|JST|cet|CET')
