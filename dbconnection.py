from sqlalchemy import create_engine
import pandas as pd
from XMLRead import X998_GrpPlatz
from datetime import datetime
import configparser


user = 'ksadmin'
password = 'ksadmin'
host = 'HOC-W10-212\SQL19'
DB = 'rtp'
driver = 'SQL Server Native Client 11.0'
DATABASE_CONNECTION = f'mssql://{user}:{password}@{host}/{DB}?driver={driver}'
engine = create_engine(DATABASE_CONNECTION)
connection = engine.connect()
# print(engine)
dateTimeObj = datetime.now()


Platz = ""
FirmaNr = ""
Show = ""

"""
config = configparser.ConfigParser()
config.read("ksmain.ini")
FirmaNumber = config.get("TerminalName")
"""


def getArbeitplazlist(X998_GrpPlatz=X998_GrpPlatz):
    arbeitplatzlist = pd.read_sql_query(
        f"""SELECT T905_Nr,T905_bez,T905_Bez2,T905_KstNr,T905_Art,T905_Typ,T905_Akkord,T905_Leist,T905_Freigabe,
        T905_ArbGrNr,T905_Img,T905_StartScreen,T905_Schleuse FROM ksalias.dbo.G905_TermPlatz INNER JOIN 
        ksalias.dbo.T905_ArbMasch ON G905_Platz = T905_nr AND G905_FirmaNr = T905_FirmaNr 
        WHERE G905_FirmaNr = 'TE' AND G905_Nr = '{X998_GrpPlatz}' AND T905_Inaktiv <> 1 ORDER BY G905_Lfdnr""",
        connection)
    return arbeitplatzlist


def getPersonaldetails(T912_Nr):
    pers_info = pd.read_sql_query(
        f"""SELECT T912_Nr,T910_Name,T910_Vorname FROM ksalias.dbo.T910_Personalliste 
        INNER JOIN ksalias.dbo.T912_PersCard ON T910_Nr = T912_PersNr WHERE T912_Nr = {T912_Nr}""",
        connection, coerce_float=False)
    # print(f"[DB] {pers_info}")
    pers_info = pers_info.iloc[0, :]  # select first record that matches
    pers_info['T912_Nr'] = str(pers_info['T912_Nr'])
    pers_info['formatted_name'] = pers_info["T910_Vorname"] + ", " + pers_info["T910_Name"]
    return pers_info


def getGemeinkosten(userid):
    last_row = pd.read_sql_query(
        f"""select top 1 T951_DatumTS, T951_PersNr, T912_Nr, T951_ArbIst
        from T951_bd1 inner join T912_PersCard on T951_BD1.T951_PersNr=T912_PersCard.T912_PersNr
        where T912_Nr='{userid}' order by T951_DatumTS desc""", connection)
    platz = last_row.loc[0, "T951_ArbIst"]
    gk_data = pd.read_sql_query(
        f"""select top 100 TA05_FA_Nr, TA05_ArtikelBez, TA06_BelegNr, TA06_Platz_Soll from KSAlias.dbo.TA05_FAK1
        inner join KSAlias.dbo.TA06_FAD1 on TA06_FirmaNr = TA05_FirmaNr and TA06_FA_Nr = TA05_FA_Nr and TA06_Platz_Soll = '{platz}'
        inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and TA21_Typ= '3' and TA21_FirmaNR = 'TE'
        order by TA06_BelegNr""", connection)
    return gk_data

def getStatustableItem(firmNo, persNo, dateTime,currentTime):
    statustableItems = pd.read_sql_query("Select Top 1000 T951_FirmaNr,T951_Satzart,T951_TagId,T951_ArbIst,T951_DatumTS,T905_Bez"
         ",case when T951_Satzart in ('G') then null else TSNxt end as TSNxt"
          ",datediff(minute,T951_DAtumts,case when TSNxt is null then case when T951_Satzart in ('G') then null else currentTime end else TSNxt end ) as T951Dauer"
         "from (Select T951_FirmaNr,T951_Satzart,T951_TagId,T951_ArbIst,T951_DatumTS,"
						"(Select Top 1 T951_DatumTS from KSAlias.dbo.T951_Buchungsdaten as b where b.T951_Firmanr = a.T951_FirmaNr"
							"and b.T951_PersNr = a.T951_PersNr and b.T951_TagId = a.T951_TagId and b.T951_DAtumts > a.T951_DatumTS"
							"and T951_Satzart not in ('N') order by b.T951_Datumts asc ) as TSNxt,T905_Bez"
			"from KSAlias.dbo.T951_Buchungsdaten as a"
			"inner join  KSAlias.dbo.T905_ArbMasch on T951_FirmaNr = firmNo and T951_PersNr =persNo  and T951_TagId = dateTime and T905_FirmaNr = T951_Firmanr"
						"and T905_Nr = T951_Arbist and T951_Satzart not in ('N')) as T951 order by T951_DatumTS asc", connection, coerce_float=False)
    return statustableItems

# Arbeitplatzlist = getArbeitplazlist(terminalNumber)
# personalname = getPersonaldetails(connection)
# DATETIME - format: YYYY-MM-DD HH:MI:SS
# statustableitemlist = getStatustableItem("01",1035,"2021-02-05 16:18:15",currentTime=dateTimeObj)
# print(Arbeitplatzlist)
# print(personalname)
# print(statustableitemlist)






personallListe = pd.read_sql_query("SELECT T910_Nr,T910_Name,T910_Vorname FROM ksalias.dbo.T910_Personalliste",
                                       connection, coerce_float=False)
personallCard = pd.read_sql_query("SELECT T912_Nr,T912_Bez,T912_PersNr FROM ksalias.dbo.T912_PersCard",
                                      connection, coerce_float=False)
# print(personalname)
# print(personallCard)
# user['T910_Name']
# username = personallCard.loc[personallCard['T912_Nr'] == 1519]
# print(username['T912_Bez'].values[0])
# should be shown when gemeinkosten buttons
# user['T910_Name']
# GKdata = pd.read_sql_query("select top 10000 TA05_FA_Nr, TA05_ArtikelBez,TA06_BelegNr from KSAlias.dbo.TA05_FAK1 "
#                          "inner join KSAlias.dbo.TA06_FAD1 on TA06_FirmaNr = TA05_FirmaNr and TA06_FA_Nr = TA05_FA_Nr and TA06_Platz_Soll =Platz "
#                          "inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and TA21_Typ= '3' and TA21_FirmaNR =FirmaNr and TA21_Show in (Show) "
#                          "order by TA06_BelegNr",connection)

# print(GKdata)

"""
Filtering of Personal Number

#FirmaNr = ""
#G905Nr = ""
PersonalNumberFilter = pd.read_sql_query("Select T910_Nr,T910_Name,T910_Vorname from KSAlias.dbo.T910_Personalliste "
                                         "inner join "
                                         "(Select T951_FirmaNr, T951_Persnr,T951_ArbIst from KSAlias.dbo.T951_Buchungsdaten "
                                         "where T951_FirmaNr = @FirmaNr and T951_TagId >= dateadd(day,-30,current_timestamp) and T951_Satzart in ('K','A') "
                                         "group by T951_FirmaNr,T951_Persnr,T951_Arbist) "
                                         "as T951 on T910_Firmanr = T951_Firmanr and T910_Nr = T951_PersNr	"
                                         "inner join KSAlias.dbo.G905_TermPlatz on G905_FirmaNr = T951_Firmanr and G905_Platz = T951_ArbIst and G905_Nr = @G905Nr "
                                         "group by T910_Nr,T910_Name,T910_Vorname",connection)
print(PersonalNumberFilter)
"""

