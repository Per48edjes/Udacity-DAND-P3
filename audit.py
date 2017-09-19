# Import dependencies
import re


# Function to clean phone numbers
def update_phoneNum(phone_num):
    '''
    Cleans phone numbers to match (xxx) xxx-xxxx phone number convention.
    Arguments:
        phone number (string)
    Returns:
        "cleaned" phone number (string)
    '''

    # Dictionary containing one-off erroneous numbers after auditing
    one_offs = {'6667011': '(415) 666-7011',
                '6677005': '(415) 667-7005',
                '8852222': '(415) 885-2222',
                '153581220': '(415) 358-1220',
                '415221366': '(415) 221-3666',
                '415 242 960': '(415) 242-0960',
                '415-929-1183 or': '(415) 929-1183',
                '415-252-855': '(415) 252-8551'
                }

    if phone_num in one_offs:
        return one_offs[phone_num]

    ## Helper function to convert letters in phone numbers to numbers
    def letters_to_numbers(phone_num):
        '''
        Cleans phone numbers that have alphabetic mnemonics 
        Arguments:
            phone number (string)
        Returns:
            "cleaned" phone number (string)
        '''
        
        # Initialize regex to look for alphabetic characters
        ph_letters_re = re.compile(r'[a-zA-Z]+')

        # Mapping letters to telephone keypad numbers
        keypad = {  "ABC": '2',
                    "DEF": '3',
                    "GHI": '4',
                    "JKL": '5',
                    "MNO": '6',
                    "PQRS": '7',
                    "TUV": '8',
                    "WXYZ": '9' }
        
        # Set up dictionary to map decoded words to words
        words_numbers_dict = {}
        
        results = ph_letters_re.findall(phone_num)
        if results:
            for word in results:
                replacement = ''
                for letter in word.upper():
                    for k, v in keypad.iteritems():
                        if letter in k:
                            replacement += v
                words_numbers_dict[word] = replacement
            
            # Substitute word with number in string
            for word in words_numbers_dict:
                repl_re = re.compile(word)
                phone_num = repl_re.sub(words_numbers_dict[word], phone_num)

            return phone_num
                    
        else:
            return phone_num


    # Strip number of all non-numeric characters after converting text to
    # digits
    stripped_num = re.sub(r'[^0-9]', '', letters_to_numbers(phone_num))


    ## Helper function that formats a stripped phone number
    def phone_num_formatter(stripped_num):
        '''
        Formats a string that's been stripped
        Arguments:
            stripped phone number (string)
        Returns:
            "cleaned" phone number (string)
        '''
        
        # Determine how to format 10-digit phone number
        def ten_digit_formatter(ten_dig_num):
            '''
            Formats string of 10 numbers into phone number convention
            '''
            
            last_four = ten_dig_num[-4:]
            middle_three = ten_dig_num[-7:-4]
            area_code = ten_dig_num[0:3]
            return "(" + area_code + ") " + middle_three + "-" + last_four        
        
        if len(stripped_num) == 10:
            return ten_digit_formatter(stripped_num)

        # Drop country prefix code
        elif len(stripped_num) == 11:
            return ten_digit_formatter(stripped_num[1:])
       
        # Lastly, check to see if erroroneous number is a one-off case
        else:
            if stripped_num in one_offs:
                return one_offs[stripped_num]
            else:
                return ''

    return phone_num_formatter(stripped_num)


# Function to standardize zip codes to 5 digit sequence
def update_zipcode(zip_code):
    '''
    Formats a string that's been stripped
    Arguments:
        zip code (string)
    Returns:
        "cleaned" zip code (string)
    '''
    
    # Regex for valid San Francisco zipcodes
    zip_re = re.compile(r'^(94\d{3})(-\d{4})?$')   
    m = zip_re.search(zip_code)

    # One-off corrections
    one_offs = {'14123': '94123',
                '41907': '94107',
                '90214': '94109',
                '95115': '94115',
                'CA': '94133',
                '94113': '94133',
                '94087': '94107',
                '94013': '94103'
                }

    # Return normal zipcodes or truncated versions of extended zipcodes
    if m and (m.group(1) not in one_offs):
        return m.group(1)
    else:
        try:
            return one_offs[zip_code]
        except:
            return zip_code[0:5]

# Function to clean unexpected street name according to mapping
def update_street_name(name):
     
    ## Ignore these "streets," as they follow special conventions
    special_streets = ["San Francisco Bicycle Route 2", "Pier 39", "SF 80 PM 4.5", "Broadway"]
    if name in special_streets:
        return name

    # Regex to find streets with address numbers in 'addr:street' tag
    ## Check for prefix and suffix numbers 
    testA_re = re.compile(r'^(#?\d+)\s(.*)')
    testB_re = re.compile(r'^(.*?)(\sSte|\sSuite)?\s(#?\d+)$')
    
    if (name not in special_streets):
        m = testA_re.search(name)
        n = testB_re.search(name)
        if m:
            name = m.group(2)
        if n:
            name = n.group(1)
    
    # Proper cases street names that do NOT start with a number
    try:
        int(name.split()[0][0])
    except:
        name = name.title()

    # Street mapping
    street_mapping = {  "St": "Street",
                        "St.": "Street",
                        "street": "Street",
                        "st": "Street",
                        "AVE": "Avenue", 
                        "Ave": "Avenue", 
                        "Ave.": "Avenue",
                        "Blvd": "Boulevard", 
                        "Blvd.": "Boulevard", 
                        "Cresc": "Crescent", 
                        "Hwy": "Highway", 
                        "Dr": "Drive", 
                        "Ln.": "Lane", 
                        "Rd": "Road", 
                        "Rd.": "Road", 
                        "Pl": "Plaza", 
                        "Bldg": "Building"
                        }
    
    # Appending specific street types to streets missing type designation
    incomplete_streetnames = {  "15th": "15th Street", 
                                "Vallejo": "Vallejo Street",
                                "Mason": "Mason Street",
                                "Pollard": "Pollard Street",
                                "South Park": "South Park Street",
                                "Van Ness": "Van Ness Avenue",
                                "Wedemeyer": "Wedemeyer Street",
                                "Hyde": "Hyde Street",
                                "Gough": "Gough Street",
                                "Post": "Post Street",
                                "Pier": "Pier 40 A",
                                "New Montgomery": "New Montgomery Street",
                                "Mission Rock": "Mission Rock Street",
                                "Pacific Avenue Mall": "Pacific Avenue",
                                "Broadway Street": "Broadway",
                                "California": "California Street",
                                "King": "King Street"
                                }
    
    if name in incomplete_streetnames:
        return incomplete_streetnames[name]

    # One-off fixes
    oneoffs = { "Cesar Chavez St St": "Cesar Chavez Street", 
                "19th & Linda San Francisco": "Linda Street", 
                "Bay And Powell": "Bay Street",
                "Multi Use Building": "Phelan Avenue", 
                "Murray Street And Justin Drive": "Justin Drive",
                "Willard North": "North Willard Street",
                "14th St, San Francisco ": "14th Street",
                "Broadway Street; Mason Street": "Mason Street",
                "One Letterman Drive": "Letterman Drive",
               }

    if name in oneoffs:
        return oneoffs[name]

    # Regex to find anomalous street types
    street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
    result_re = re.search(street_type_re, name)
    
    if result_re:
        result = result_re.group()
        i = name.find(result)

        # Check street against street mapping; perform necessary adjustments
        if result in street_mapping:
            new_ending = street_mapping[result]
            return name[:i] + new_ending
        # Returns name as-is if it passes checks above
        else:
            return name
    else:
        return name
