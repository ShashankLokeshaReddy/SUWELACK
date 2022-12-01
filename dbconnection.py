from sqlalchemy import create_engine
import pandas as pd
from XMLRead import X998_GrpPlatz, FirmaNr
from datetime import datetime


user = 'ksadmin'
password = 'ksadmin'
host = 'HOC-W10-212\SQL19'
DB = 'rtp'
driver = 'SQL Server Native Client 11.0'
DATABASE_CONNECTION = f'mssql://{user}:{password}@{host}/{DB}?driver={driver}'
engine = create_engine(DATABASE_CONNECTION)
connection = engine.connect()

def getArbeitplazlist():
    arbeitplatzlist = pd.read_sql_query(
        f"""SELECT T905_Nr,T905_bez,T905_Bez2,T905_KstNr,T905_Art,T905_Typ,T905_Akkord,T905_Leist,T905_Freigabe,
        T905_ArbGrNr,T905_Img,T905_StartScreen,T905_Schleuse FROM ksalias.dbo.G905_TermPlatz INNER JOIN 
        ksalias.dbo.T905_ArbMasch ON G905_Platz = T905_nr AND G905_FirmaNr = T905_FirmaNr 
        WHERE G905_FirmaNr = '{FirmaNr}' AND G905_Nr = '{X998_GrpPlatz}' AND T905_Inaktiv <> 1 ORDER BY G905_Lfdnr""",
        connection)
    return arbeitplatzlist

def getArbeitplatzBuchung():
    arbeitplatzlist = pd.read_sql_query(
        f"""Select T905_Nr,T905_Bez from T905_ArbMasch inner join G905_TermPlatz on T905_FirmaNr = '{FirmaNr}'  and G905_FirmaNr = T905_FirmaNr and G905_Platz = T905_nr  and G905_Nr = '{X998_GrpPlatz}'""",
        connection)
    persnr = pd.read_sql_query(
        f"""Select * from ksmaster.dbo.kstf_T910G905Bu('{FirmaNr}','{X998_GrpPlatz}')""",
        connection)
    persnr["T910_Name"] = persnr['T910_Name'].astype(str) +" "+ persnr["T910_Vorname"]
    fanr = pd.read_sql_query(
        f"""Select TA06_FA_Nr,TA05_ArtikelBez  from TA06_FAD1  inner join TA21_AuArt on TA21_FirmaNr = '{FirmaNr}' and TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and (TA21_Typ in ('3') or  TA06_FA_Art = '02') inner join G905_TermPlatz on G905_FirmaNr = TA06_FirmaNr and G905_Platz = TA06_Platz_soll and G905_Nr = '{X998_GrpPlatz}' inner join TA05_FAK1 on TA05_FirmaNr = TA06_FirmaNr and TA05_FA_Nr = TA06_FA_nr group by TA06_FA_nr,TA05_ArtikelBez  order by TA06_FA_Nr""",
        connection)
    return [arbeitplatzlist, persnr, fanr]

def getPersonaldetails(T912_Nr):
    pers_info = pd.read_sql_query(
        f"""SELECT T912_Nr,T910_Name,T910_Vorname,T910_Nr FROM ksalias.dbo.T910_Personalliste 
        INNER JOIN ksalias.dbo.T912_PersCard ON T910_Nr = T912_PersNr WHERE T912_Nr = {T912_Nr}""",
        connection, coerce_float=False)
    pers_info = pers_info.iloc[0, :]  # select first record that matches
    pers_info['T912_Nr'] = str(pers_info['T912_Nr'])
    pers_info['formatted_name'] = pers_info["T910_Vorname"] + ", " + pers_info["T910_Name"]
    return pers_info


def getLastbooking(userid):
    last_booking = pd.read_sql_query(
        f"""select top 1 T951_DatumTS, T951_PersNr, T912_Nr, T951_ArbIst
        from T951_bd1 inner join T912_PersCard on T951_BD1.T951_PersNr=T912_PersCard.T912_PersNr
        where T912_Nr='{userid}' order by T951_DatumTS desc""", connection)
    return last_booking


def getGemeinkosten(userid):
    last_booking = getLastbooking(userid)
    platz = last_booking.loc[0, "T951_ArbIst"]
    gk_data = pd.read_sql_query(
        f"""select top 100 TA05_FA_Nr, TA05_ArtikelBez, TA06_BelegNr, TA06_Platz_Soll from KSAlias.dbo.TA05_FAK1
        inner join KSAlias.dbo.TA06_FAD1 on TA06_FirmaNr = TA05_FirmaNr and TA06_FA_Nr = TA05_FA_Nr and TA06_Platz_Soll = '{platz}'
        inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and TA21_Typ= '3' and TA21_FirmaNR = '{FirmaNr}'
        order by TA06_BelegNr""", connection)
    return gk_data


def getStatustableitems(userid):
    persnr = getPersonaldetails(userid)['T910_Nr']
    date = datetime.now().strftime("%Y-%d-%m")
    ts_now = datetime.now().strftime("%Y-%d-%m %H:%M:%S")
    last_booking = getLastbooking(userid)
    platz = last_booking.loc[0, "T951_ArbIst"]
    upper_items = pd.read_sql_query(f"""SELECT * FROM ksmaster.dbo.kstf_T951BD1_Info('{FirmaNr}', {persnr}, '{date}')""",
                                    connection)
    lower_items = pd.read_sql_query(
        f"""SELECT * FROM ksmaster.dbo.kstf_TA55TA51_InfoAllFB1('{FirmaNr}', {persnr}, '{platz}', '{date}', '{ts_now}')""",
        connection)

    # create new dataframes for the necessary columns
    upper_items_df = pd.DataFrame(columns=['Aktion', 'Arbeitplatz', 'Bezeichnung', 'Von', 'Bis', 'Dauer'])
    upper_items_df["Aktion"] = upper_items.loc[:, "T951_Satzart"]
    # replace K and G strings with Gekommen and Gegangen
    upper_items_df["Aktion"] = upper_items_df["Aktion"].str.replace("K","0", regex=False)
    upper_items_df["Aktion"] = upper_items_df["Aktion"].str.replace("G","1", regex=False)
    upper_items_df["Aktion"] = upper_items_df["Aktion"].str.replace("A","2", regex=False)
    upper_items_df["Aktion"] = upper_items_df["Aktion"].str.replace("0","Gekommen", regex=False)
    upper_items_df["Aktion"] = upper_items_df["Aktion"].str.replace("1","Gegangen", regex=False)  
    upper_items_df["Aktion"] = upper_items_df["Aktion"].str.replace("2","Wechselbuchung", regex=False)        
    upper_items_df["Arbeitplatz"] = upper_items.loc[:, "T951_ArbIst"]
    upper_items_df["Bezeichnung"] = upper_items.loc[:, "T905_Bez"]
    upper_items_df["Von"] = upper_items.loc[:, "T951_DatumTS"]
    upper_items_df["Bis"] = upper_items.loc[:, "TSNxt"].astype(str).replace("NaT", "")
    upper_items_df["Dauer"] = upper_items.loc[:, "T951Dauer"]

    lower_items_df = pd.DataFrame(columns=['Auftrag', 'Arbeitplatz', 'Bezeichnung', 'Von', 'Bis', 'Dauer', 'Menge', 'Auftragsstatus', 'Pers.Nr'])
    lower_items_df["Auftrag"] = lower_items.loc[:, "TA06_BelegNr"]      
    lower_items_df["Arbeitplatz"] = lower_items.loc[:, "TA51_Platz_Ist"]
    lower_items_df["Bezeichnung"] = lower_items.loc[:, "TA06_AgBez"]
    lower_items_df["Von"] = lower_items.loc[:, "TA51_AnfangTS"]
    lower_items_df["Bis"] = lower_items.loc[:, "TA51_EndeTS"].astype(str).replace("NaT", "")
    lower_items_df["Dauer"] = lower_items.loc[:, "TA51_DauerTS"]
    lower_items_df["Menge"] = lower_items.loc[:, "TA51_MengeIstGut"]
    lower_items_df["Auftragsstatus"] = lower_items.loc[:, "TA51_Auf_Stat"]
    lower_items_df["Pers.Nr"] = lower_items.loc[:, "TA51_PersNr"].astype(int)

    return [upper_items_df, lower_items_df]
