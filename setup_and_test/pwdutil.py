import base64
import argparse
import pickle
import pathlib

CONFIG_LOC =  pathlib.Path(pathlib.Path.cwd(),"./config/")  
KEY_LOC =  pathlib.Path(pathlib.Path.cwd(),"./config/") 

PWD_FILE = pathlib.Path(CONFIG_LOC, ".pwd.bin")
KEY_FILE = pathlib.Path(KEY_LOC, ".key.txt")

def get_key():
    try:
        with open(KEY_FILE,"r") as f:
            key = str(f.readlines())
        return key
    
    except Exception as e:
        print(f"Can't locate key, exiting {e}")
        exit(1)
    
def encode(key, cleartext):
    encoded = []
    for i in range(len(cleartext)):
        key_c = key[i % len(key)]
        enc_c = (ord(cleartext[i]) + ord(key_c)) % 256
        encoded.append(enc_c)
    encoded_bytes = bytes(encoded)
    return base64.urlsafe_b64encode(encoded_bytes)

def decode(key, enc):
    dec = []
    decoded_bytes = base64.urlsafe_b64decode(enc)

    for i in range(len(decoded_bytes)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + decoded_bytes[i] - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)

def store_pwd(encoded):
    try:
        with open(PWD_FILE,"wb") as f:
            pickle.dump(encoded, f)
    except Exception as e:
        print(f"Error in storing password: {e}")
        

def get_pwd():
    try:
        with open(PWD_FILE, "rb") as f:
            encoded = pickle.load(f)
        return encoded
    
    except FileNotFoundError:
        print(f"Password file not found: {PWD_FILE}")
        return None
    
    except Exception as e:
        print(f"Error retreiving password: {e}")
        return None

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Password Config Util", formatter_class= argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--set", dest = "password", help = "Store encoded password")
    group.add_argument("-g","--get", dest = "get", help = "Get encoded password", action = "store_true")
    
    args = vars(parser.parse_args())    
    key = get_key()

    if args["password"]:
        print("Saving Encoded Password")
        encoded = encode(key, args["password"])
        store_pwd(encoded)

    elif args["get"]:
        print("Get Encoded Password")
        encoded = get_pwd()

        if encoded:
            decoded = decode(key, encoded)
            print(decoded)
        else:
            print("Error - Password not found")

    else:
        print("Error - Unknown Option")
        parser.print_usage()
        exit(1)