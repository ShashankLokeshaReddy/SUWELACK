from sqlalchemy import create_engine
import pandas as pd
from XMLRead import terminalNumber
import configparser


user = 'ksadmin'
password = 'ksadmin'
host = 'HOC-W10-212\SQL19'
DB = 'ksmaster'
driver = 'SQL Server Native Client 11.0'
DATABASE_CONNECTION = f'mssql://{user}:{password}@{host}/{DB}?driver={driver}'
engine = create_engine(DATABASE_CONNECTION)
connection = engine.connect()
# print(engine)


Platz = ""
FirmaNr = ""
Show = ""

"""
config = configparser.ConfigParser()
config.read("ksmain.ini")
FirmaNumber = config.get("TerminalName")
"""

def getArbeitplazlist(connection):
    arbeitplatzlist = pd.read_sql_query("SELECT T905_Nr,T905_bez,T905_Bez2,T905_KstNr,T905_Art,T905_Typ,T905_Akkord,T905_Leist,T905_Freigabe,T905_ArbGrNr,T905_Img,T905_StartScreen,T905_Schleuse "
                                   "FROM rtp.dbo.G905_TermPlatz INNER JOIN rtp.dbo.T905_ArbMasch ON G905_Platz = T905_nr AND G905_FirmaNr = T905_FirmaNr "
                                   "WHERE G905_FirmaNr = 'TE' AND G905_Nr =? AND T905_Inaktiv <>1 "
                                   "ORDER BY G905_Lfdnr", connection, params=[terminalNumber])
    return arbeitplatzlist



def getPersonaldetails(connection):
    personalname = pd.read_sql_query("SELECT T912_Nr,T910_Name,T910_Vorname FROM rtp.dbo.T910_Personalliste "
                                     "INNER JOIN rtp.dbo.T912_PersCard ON T910_Nr = T912_PersNr", connection, coerce_float=False)
    personalname['T912_Nr'] = personalname['T912_Nr'].astype("string")
    personalname['VorNameName'] = personalname["T910_Vorname"] + ", " + personalname["T910_Name"]
    return personalname


Arbeitplatzlist = getArbeitplazlist(connection)
personalname = getPersonaldetails(connection)
print(Arbeitplatzlist)
print(personalname)






personallListe = pd.read_sql_query("SELECT T910_Nr,T910_Name,T910_Vorname FROM rtp.dbo.T910_Personalliste",
                                       connection, coerce_float=False)
personallCard = pd.read_sql_query("SELECT T912_Nr,T912_Bez,T912_PersNr FROM rtp.dbo.T912_PersCard",
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
