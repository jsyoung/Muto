'''
Created on Jan 27, 2013

@author: jyoung
'''
import numpy as np

def read(ob):
    '''
    Read and translate a single Vaisala CL31 message 2(?) observation text
    as reported directly from the ceilometer.
    
    Parameters
    ----------
    ob: str
        the text that is returned by the ceilometer between the begin comms 
        and end comms control characters (unichr(001 - 004))
    
    Returns
    -------
    dict : 'bs', 'height', 'status'
        bs: the range corrected un-scaled (assuming a scale of 1e9) log10'd bs
            coefficient
        'height': range indices for the non-time dimension of the output 
            corresponding to the vertical data key
        'status': 13 transcribed floating point numbers which give cloud height
            information, and status information. It is possible to get more
            information from these lines with a revision of this code.
    '''
    OB_LENGTH = 770  # FIXME - the current return length is limited to 770
    SCALING_FACTOR = 1.0e9
    'break the full ob text into it\'s constituent parts'
    p1 = ob.split(unichr(002))
    p2 = p1[1].split(unichr(003))
    code = p1[0].strip()
    ob = p2[0].strip()  # just contents between B and C
    # unused currently checksum = p2[1].strip()

    data = ob.split("\n")  # split into lines

    'the last line of the profile should be the data line'
    prof = data[-1].strip()
    'grab status lines'
    sl1 = data[0].strip()
    sl2 = data[-2].strip()  # I will skip any intermediate data lines...

    status = np.array([sl1[0].replace('/', '0'),
                    sl1[1].replace('A', '2').replace('W', '1')] +
                    sl1[2:-13].replace('/', '0').split() + sl2[:-14].split(),
                    dtype=np.float32)
    'status should have a length of 13... we shall see...'
    # determine height difference by reading the last digit of the code
    height_codes = [0, 10, 20, 5, 5]  # '0' is not a valid key, and will not happen
    data_lengths = [0, 770, 385, 1500, 770]
    'length between 770 and 1500'
    datLen = data_lengths[int(code[-1])]
    htMult = height_codes[int(code[-1])]
    values = np.zeros(datLen, dtype=np.float32)
    ky = 0
    for i in xrange(0, len(prof), 5):

        ven = prof[i:i + 5]
        if ven[0:2] == "ff" or ven == '00000':
            # logic: ff corresponds to >=ff000, which is ~1e6, which is beyond super high
            values[ky] = 1
        else:
            values[ky] = int(ven, 16)  # scaled to 100000sr/km (x1e9 sr/m)FYI
        ky += 1  # keep the key up to date

    # then the storage will be log10'd values
    out = {
        'height':np.arange(0, 10000, htMult)[:OB_LENGTH],
        'bs':np.log10(values[:OB_LENGTH] / SCALING_FACTOR),
        'status':status
        }
    return out

def decode_hex_string(string, fail_value=1, char_count=5):
    '''
    This is a compacted code for simply reading the hexadecimal string provided
    which comes from a CL31, or 51 message. It cannot compensate for
    entries with newlines (see the CT12 module for that).
    
    Parameters
    ----------
    string: str
        the newline/index free string which will be read for individual 5-digit
        hexadeceimal values. Standard extreme-value logic is applied.
        
    fail_value: int, optional
        the value assigned to supposedly unrealistic values
        
    char_count: int, optional
        the number of characters per value in the string. For a CL31 this is 5

    Returns
    -------
    numpy array of directly translated values, not scaled. fail high values are 
    set to 1, as this value is often lower than any other. You can adjust this
    value if you wish it to be something else. Negative values will incur NaNs.
    '''
    data_len = len(string)
    data = np.zeros(data_len / 5, dtype=int)
    key = 0
    for i in xrange(0, data_len, 5):
        temp = string[i:i + 5]
        if temp[0:2] == "ff" or temp == '00000':
            # logic: ff corresponds to >=ff000, which is ~1e6, which is preposterous
            data[key] = fail_value
        else:
            data[key] = int(temp, 16)  # scaled to 100000sr/km (x1e9 sr/m)FYI

        key += 1  # keep the key up to date
    return data

