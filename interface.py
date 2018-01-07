import argparse, getpass
from support import __title__, __version__, __author__, mosquitoauthdb

authdb_address = 'localhost'
authdb_db = 'bnblock'
authdb_username = 'mosquitto'
authdb_password = 'EAmyFuWVJEgTMhKMt2hGVnrL'

def setup_user():
    authdb = mosquitoauthdb.Connect(authdb_address, authdb_db, authdb_username, authdb_password)
    print("\nbnbLock User Registration\n-------------------------\n")
    username = get_username(authdb)
    firstname = get_name("First")
    lastname = get_name("Last")
    password = get_password()
    confirm = confirm_details(username, firstname, lastname)
    if confirm:
        print("Adding user......")
        name = "{} {}".format(firstname, lastname)
        authdb.append_user(username, password, name)
        if authdb.check_user(username):
            print("User added!")
        else:
            print("Failed to add...")

def confirm_details(username, firstname, lastname):
    print("\nConfirm User Information\n------------------------")
    print("    Username: {}".format(username))
    print("  First Name: {}".format(firstname))
    print("   Last Name: {}".format(lastname))
    print("------------------------\n")
    print("Is this information correct (Y/n)?")
    response = str(input(": "))
    if response.lower() == "y":
        return True
    elif response.lower() == "n":
        return False

def get_username(authdb, check=True):
    try:
        username = str(input('Username: '))
        char_val = [ord(c) for c in username]
        invalid_chars = list()
        for char in char_val:
            if char == 45 or char == 46 or char == 95:
                continue
            elif char >= 48 and char <= 57:
                continue
            elif char >= 65 and char <= 90:
                continue
            elif char >= 97 and char <= 122:
                continue
            else:
                invalid_chars.append(char)
        if invalid_chars != []:
            raise (InvalidUsernameException(invalid_chars, 0))
        elif username.__len__() > 16 or username.__len__() == 0:
            raise (InvalidUsernameException(username.__len__(), 1))
        if check:
            if authdb.check_user(username):
                raise (InvalidUsernameException(username, 2))
        if not check:
            if not authdb.check_user(username):
                raise (InvalidUsernameException(username, 3))
        return username
    except InvalidUsernameException as e:
        if e.errors == 0:
            print("\n")
            for char in e.message:
                print("  ERROR: '{}' Not accepted.".format(chr(char)))
            print("\n  A-Z, a-z, 0-9, '-', '.', '_' is acceptable.\n")
        elif e.errors == 1:
            print("\n  ERROR: Username length must be 1-16 characters long.\n")
        elif e.errors == 2:
            print("\n  ERROR: '{}' is already taken.\n".format(e))
        elif e.errors == 3:
            print("\n  ERROR: '{}' does not exist.\n".format(e))
        return get_username(authdb)

def name_check(name):
    abc_count = 0
    misc_count = 0
    char_val = [ord(c) for c in name]
    for char in char_val:
        if char <= 64:
            misc_count += 1
        elif 65 <= char <= 90:
            abc_count += 1
        elif 91 <= char <= 96:
            misc_count += 1
        elif 97 <= char <= 122:
            abc_count += 1
        else:
            misc_count += 1
    if misc_count > 0:
        raise (InvalidUsernameException("\n  ERROR: Invalid characters used. Use (a-b, A-B)\n", 0))
    elif name.__len__() >= 16 or name.__len__() < 1:
        raise (InvalidUsernameException("\n  ERROR: Invalid name length. (1-16)\n", 1))

def get_name(prompt):
    try:
        name = input('{} Name: '.format(prompt))
        name_check(name)
        return name
    except InvalidUsernameException as e:
        print(e)
        return get_name(prompt)

def password_check(password):
    char_val = [ord(c) for c in password]
    abc_count = 0
    ABC_count = 0
    spc_count = 0
    dig_count = 0
    invalid = list()
    for char in char_val:
        if char >= 33 and char <= 47:
            spc_count += 1
        elif char >= 48 and char <= 57:
            dig_count += 1
        elif char >= 58 and char <= 64:
            spc_count += 1
        elif char >= 65 and char <= 90:
            ABC_count += 1
        elif char >= 91 and char <= 96:
            spc_count +=1
        elif char >= 97 and char <= 122:
            abc_count += 1
        elif char >= 123 and char <= 126:
            spc_count += 1
        else:
            invalid.append(chr(char))

    if invalid != []:
        raise (InvalidUsernameException("\n  ERROR: Illegal characters used.\n", 3))
    if abc_count < 1 or ABC_count < 1 or spc_count < 1 or dig_count < 1:
        raise (InvalidUsernameException("\n  ERROR: Must include at least one of each: lowercase letter, uppercase letter, number, and special character.\n", 4))

def get_password():
    try:
        password = getpass.getpass()
        password_check(password)
        if password.__len__() < 9 or password.__len__() > 60:
            raise (InvalidUsernameException("\n  ERROR: Password length. (Must be at least 9-60 characters long)\n",1))
        confirm_passsword = getpass.getpass("Confirm Password: ")
        if password != confirm_passsword:
            raise (InvalidUsernameException("\n  ERROR: Passwords do not match.\n", 2))
        return password
    except InvalidUsernameException as e:
        print(e)
        return get_password()

class InvalidUsernameException(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors
        self.message = messag2

def main():
    parser = argparse.ArgumentParser(prog=__title__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('-s', '--setup', help='Initializes db for daemon.', action='store_true', required=False)
    parser.add_argument('-n', '--new', help='Add new user to bnbLock Network.', action='store_true', required=False)
    parser.add_argument('-r', '--run', help='Runs mqtt network daemon.', action='store_true',
                        required=False),
    parser.add_argument('-R', '--remove', help='Remove user from bnbLock network.', action='store_true',
                        required=False)
    args = parser.parse_args()
    if args.new:
        setup_user()
    if args.remove:
        authdb = mosquitoauthdb.Connect(authdb_address, authdb_db, authdb_username, authdb_password)
        print("Account Removal Wizard\n----------------------\n")
        username = get_username(authdb, check=False)
        authdb.remove_bnblock_user(username)
        authdb.save()
    if args.setup:
        mosquitoauthdb.setup_database(authdb_address,authdb_username,authdb_password,authdb_db)
if __name__ == '__main__':
    main()