url_parse_match = r'^((http[s]?|ftp):\/)?\/?([^:\/\s]+)((\/\w+)*\/)([\w\-\.]+[^#?\s]+)(.*)?(#[\w\-]+)?$' # https://pythex.org/?regex=%5E((http%5Bs%5D%3F%7Cftp)%3A%5C%2F)%3F%5C%2F%3F(%5B%5E%3A%5C%2F%5Cs%5D%2B)((%5C%2F%5Cw%2B)*%5C%2F)(%5B%5Cw%5C-%5C.%5D%2B%5B%5E%23%3F%5Cs%5D%2B)(.*)(%23%5B%5Cw%5C-%5D%2B)%3F%24&test_string=https%3A%2F%2Fgroceries.asda.com%2Fproduct%2Fnatural-plain-organic%2Ffage-total-fat-free-greek-recipe-natural-yogurt%2F24771357&ignorecase=0&multiline=0&dotall=0&verbose=0
url_match_full = r'^(?:(?:http[s]?|ftp):\/)?\/?(?:[^:\/\s]+)(?:(?:\/\w+)*\/)(?:[\w\-\.]+[^#?\s]+)(?:.*)?(?:#[\w\-]+)?$' #Just added non-capturing groups for now.
url_match_try = '[A-Za-z]+:\/\/[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_:%&;\?\#\/.=]+' # https://pythex.org/?regex=%5E((%3F%3A(%3F%3Ahttp%5Bs%5D%3F%7Cftp)%3A%5C%2F)%3F%5C%2F%3F(%3F%3A%5B%5E%3A%5C%2F%5Cs%5D%2B)(%3F%3A(%3F%3A%5C%2F%5Cw%2B)*%5C%2F)(%3F%3A%5B%5Cw%5C-%5C.%5D%2B%5B%5E%23%3F%5Cs%5D%2B))%5C%3F(%5B%5Cw%5Cd%5D%2B%3D%5B%5Cw%5Cd%5D%2B%26%3F)%2B(%3F%3A.*)(%3F%3A%23%5B%5Cw%5C-%5D%2B)%3F%24&test_string=https%3A%2F%2Fgroceries.asda.com%2Fproduct%2Fnatural-plain-organic%2Ffage-total-fat-free-greek-recipe-natural-yogurt%2F24771357%3Fsid%3D12534Q%26style%3Dgreen&ignorecase=0&multiline=0&dotall=0&verbose=0
reNoCapt = ''
reCondProtcl = ''
URL_DOMAIN_MATCH = r'^(({0}({0}http[s]?|ftp):\/\/){1}({0}[^:\/\s]+))'.format(reNoCapt, reCondProtcl)
URL_PATH_MATCH = r'^(({0}\/[\w-]+))'.format(reNoCapt)
URL_QUERY_FLAG_MATCH = r'^\?|\/\?'
URL_QUERY_KEY_MATCH = r'^(?:&)?([^\=\&]+)'
URL_QUERY_VALUE_MATCH = r'^(?:=)([^\=\&]+)'