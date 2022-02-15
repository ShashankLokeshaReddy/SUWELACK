import clr
import sys
import os


sys.path.append("dll/bin")
clr.AddReference("kt002_PersNr")
from kt002_persnr import kt002

os.chdir("dll/bin")
kt002.Init()
kt002.InitTermConfig()



def get_kommen_gehen(scan_value, check_fa=False):
    """
    Cleans given scan_value, checks if given value is PNr and identifies appropriate next satzart & bufunction.

    Args:
        scan_value: scanned value of chip. Should be a T912_PersCardNr.
        check_fa: whether it should be checked if given scan_value is a Fertigungsauftrag.

    Returns:
        The cleaned scan_value, the appropriate next satzart and the according bufunc.

    Raises:
        ValueError: Is raised if scanned value is not a valid T912 number or bufunc is invalid.
    """

    show_nr = kt002.ShowNumber(scan_value, '', 0, 1, 1, '', check_fa, '', 6)
    # print(f"show_nr: {show_nr}")
    nr, check_fa, satzart, bufunc = show_nr
    check_pnr = kt002.Pruef_PNr(check_fa, nr, satzart, bufunc)
    # print(f"check_pnr: {check_pnr}")
    nr_valid, satzart, bufunc = check_pnr

    if not nr_valid:
        raise ValueError("[DLL] Eingescannter Wert ist keine gültige T912 Nummer.")

    check_pnrfunc = kt002.Pruef_PNrFkt(bufunc, 0, satzart, 0, 1, 1, "", "")
    # print(f"check_pnrfunc: {check_pnrfunc}")
    bufunc_valid, satzart, buaction, activefkt, msg = check_pnrfunc

    if not bufunc_valid:
        raise ValueError("[DLL] Buchungsfunktion ungültig.")

    return nr, satzart, bufunc  # Example: '1024', 'K', 0



def buchen_kommen_gehen(nr, satzart, t905nr='', kst='1001', kstk=0):
    """
    Checks in/out user given from nr according to satzart onto given workstation.

    Args:
        nr: Scanned and cleaned T912_PersCardNr for person to be booked.
        satzart: What kind of booking to do. [K]ommen, [G]ehen, [A]rbeitsplatzwechsel, [Z]Pause, [I]nfo
        t905nr: T905Nr of workstation to book onto if satzart="K"
        kst: Book work onto a Kostenstelle (deperecated).
        kstk: Where to look for workstation. 0: take from Personalstamm,
            1: take last booked station, 2: take from given t905nr, 3: take from default station near terminal

    Returns:
        The T905Nr of workstation that user has been booked onto if satzart="K"
        The T905Nr of workstation that user has left if satzart="G"
        None if action was canceled.
    """

    # checks whether FA was scanned
    verify_booking = kt002.BuAkt_Buchung(satzart, t905nr, 1, '', 1, 0, 0, 0)
    dialogue, satzart, t905nr, buaction, t22duration, booking_type = verify_booking

    if dialogue:
        # action was canceled by user
        return None

    # start of booking process?
    check_in_out_booking = kt002.PNR_Buch(satzart, kst, t905nr, '', '', '', kstk)
    dialogue, _, kst, workstation, day, kstk = check_in_out_booking
    print(f"[DLL] check_in_out_booking: {check_in_out_booking}")

    if dialogue:
        # action was canceled by user
        return None

    if satzart == 'K':
        print("[DLL] Dialog: Arbeitsplatz eingeben")
        # check in booking
        dialogue = ''
    elif satzart == 'G':
        print("[DLL] Dialog: Wollen sie wirklich gehen?")
        # check out booking
        check_out_res = kt002.PNR_Buch2Geht()  # <- NOT YET IMPLEMENTED
            # checks if Gemeinkosten still running and should be ended
        dialogue = ''

    if dialogue:
        # action was canceled by user
        return None
    else:
        # insert check in/out booking to database
        final_booking = kt002.PNR_Buch3(day, satzart, kst, workstation, '', '', 0)

    # clear booking for next booking
    clear_booking = kt002.PNR_Buch4Clear(1, nr, satzart, workstation, buaction, True, '', '', '', '', '')

    return workstation  # Example: 'G012'


def change_workstation(nr, t905nr, kst='1001', kstk=2):
    """
    Changes workstation for user given from nr .

    Args:
        nr: Scanned and cleaned T912_PersCardNr for person to be booked.
        satzart: What kind of booking to do. [K]ommen, [G]ehen, [A]rbeitsplatzwechsel, [Z]Pause, [I]nfo
        t905nr: T905Nr of workstation to book onto.
        kst: Book work onto a Kostenstelle (deperecated).
        kstk: Where to look for workstation. 0: take from Personalstamm,
            1: take last booked station, 2: take from given t905nr, 3: take from default station near terminal

    Returns:
        The T905Nr of workstation that user has been booked onto.
        None if action was canceled.
    """

    verify_booking = kt002.BuAkt_Buchung('A', t905nr, 1, '', 1, 0, 0, 0)
    dialogue, satzart, t905nr, buaction, t22duration, booking_type = verify_booking

    # start of booking process
    change_ws_booking = kt002.PNR_Buch('A', kst, t905nr, '', '', '', kstk) # add documentation for input values)
    dialogue, satzart, kst, workstation, day, kstk = change_ws_booking
    print(f"[DLL] change_ws_booking: {change_ws_booking}")

    if dialogue:
        # action was canceled by user
        return None

    # use kt002.PNR_Buch2Geht() here to log out from previous workstation
    check_out_res = kt002.PNR_Buch2Geht()

    # confirm/save workstation change
    final_booking = kt002.PNR_Buch3(day, 'A', kst, workstation, '', '', 0)

    # clear booking for next booking
    clear_booking = kt002.PNR_Buch4Clear(1, nr, 'A', workstation, 1, True, '', '', '', '', '')

    return workstation  # Example: 'G012'


# Test

# nr, satzart, bufunc = get_kommen_gehen(scan_value="1024")
# print(nr, satzart, bufunc)

# if satzart == "K":
    # If person should come, specify workstation (t905nr)
    # workstation = buchen_kommen_gehen(nr, satzart, t905nr="F101")
# elif satzart == "G":
    # If person should go, don't specify workstation (checks out from the one the person has used)
    # workstation = buchen_kommen_gehen(nr, satzart)

# print(workstation)

# method to change workstation (only run if person is currently checked in), specify workstation with t905nr
# print("Dialog: Arbeitsplatz wechseln")
# new_workstation = change_workstation(nr, t905nr="G012")

