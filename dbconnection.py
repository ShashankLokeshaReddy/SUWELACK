from sqlalchemy import create_engine
import pandas as pd



user = 'ksadmin'
password = 'ksadmin'
host = 'HOC-W10-212\SQL19'
DB = 'ksmaster'
driver ='SQL Server Native Client 11.0'
DATABASE_CONNECTION = f'mssql://{user}:{password}@{host}/{DB}?driver={driver}'
engine = create_engine(DATABASE_CONNECTION)
connection = engine.connect()
print(engine)


Platz=""
FirmaNr= ""
Show = 0


data = pd.read_sql_query("select top 10000 TA05_FA_Nr, TA05_ArtikelBez,TA06_BelegNr from KSAlias.dbo.TA05_FAK1 "
                         "inner join KSAlias.dbo.TA06_FAD1 on TA06_FirmaNr = TA05_FirmaNr and TA06_FA_Nr = TA05_FA_Nr and TA06_Platz_Soll =Platz "
                         "inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and TA21_Typ= '3' and TA21_FirmaNR =FirmaNr and TA21_Show in (Show) "
                         "order by TA06_BelegNr",connection)

print(data)