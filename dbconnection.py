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

"""
Platz=""
#FirmaNr= "TE"
Show = ""


GKdata = pd.read_sql_query("select top 10000 TA05_FA_Nr, TA05_ArtikelBez,TA06_BelegNr from KSAlias.dbo.TA05_FAK1 "
                         "inner join KSAlias.dbo.TA06_FAD1 on TA06_FirmaNr = TA05_FirmaNr and TA06_FA_Nr = TA05_FA_Nr and TA06_Platz_Soll =Platz "
                        "inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and TA21_Typ= '3' and TA21_FirmaNR =FirmaNr and TA21_Show in (Show) "
                      "order by TA06_BelegNr",connection)
#
#print(GKdata)

"""
#Filtering of Personal Number
"""
FirmaNr = "TE"
G905Nr = ""
PersonalNumberFilter = pd.read_sql_query("Select T910_Nr,T910_Name,T910_Vorname from KSAlias.dbo.T910_Personalliste "
                                        "inner join "
                                        "(Select T951_FirmaNr, T951_Persnr,T951_ArbIst from KSAlias.dbo.T951_Buchungsdaten "
                                        "where T951_FirmaNr = 'TE' and T951_TagId >= dateadd(day,-30,current_timestamp) and T951_Satzart in ('K','A') "
                                        "group by T951_FirmaNr,T951_Persnr,T951_Arbist) "
                                       "as T951 on T910_Firmanr = T951_Firmanr and T910_Nr = T951_PersNr	"
                                        "inner join KSAlias.dbo.G905_TermPlatz on G905_FirmaNr = T951_Firmanr and G905_Platz = T951_ArbIst and G905_Nr = @G905Nr"
                                         "group by T910_Nr,T910_Name,T910_Vorname",connection)
#
#print(PersonalNumberFilter)
#DEU
#ENG
#sp1
#PT
#PTx
#üt
SELECT TOP (1000) [S903_ID]
      ,[S903_Sprachkn]
      ,[S903_Text]
      ,[S903_TextTyp]
      ,[S903_Anlage]
      ,[S903_Aenderung]
      ,[S903_User]

  FROM [rtp].[dbo].[S903_Sprache_K] where [S903_Sprachkn] = 'DEU';
"""
#languagetable= pd.read_sql_query("Select S903_ID,S903_Sprachkn,S903_Text,S903_TextTyp,S903_Aenderung,S903_User from rtp.dbo.S903_Sprache_K",connection)
#print(languagetable)

sprachetable = pd.read_sql_query("Select S903_ID,S903_Sprachkn,S903_Text,S903_TextTyp,S903_Aenderung,S903_User from rtp.dbo.S903_Sprache",connection)
print(sprachetable)

#DEUtable = sprachetable.loc[sprachetable['S903_Sprachkn'] == "DEU"]
#print(DEUtable)
"""
messageFile = open("messages.pot","w")
messageFile.write("# Translations template for PROJECT."
                 "Content-Type: text/plain; charset=utf-8\n"
                 "Content-Transfer-Encoding: 8bit\n")
for index, row in DEUtable.iterrows():
                    messageFile.write('msgid "%s"' % row['S903_Text'] + '\nmsgstr ""\n' )
messageFile.close()
"""
current= sprachetable.iloc[0]["S903_ID"]
next = sprachetable.iloc[1]["S903_ID"]
print(current)
print(next)
eng =[]
deu =[]
sp =[]
pt =[]

#messageFile = open("translation.csv","w")
ptfile = open("translations/pt/LC_MESSAGES/messages.po","w")
enfile = open("translations/en/LC_MESSAGES/messages.po","w")
for items in range(len(sprachetable)-1):
    if sprachetable.iloc[items]["S903_ID"] == sprachetable.iloc[items+1]["S903_ID"]:
        #messageFile.write(sprachetable.iloc[items]["S903_ID"]+",")
        if sprachetable.iloc[items]["S903_Sprachkn"] =="DEU":
            #print(sprachetable.iloc[items]["S903_Text"])
            deu.append(sprachetable.iloc[items]["S903_Text"])
            ptfile.write('msgid "%s"' % sprachetable.iloc[items]["S903_Text"] + '\n')
            enfile.write('msgid "%s"' % sprachetable.iloc[items]["S903_Text"] + '\n')
            #messageFile.write(sprachetable.iloc[items]["S903_Text"]+",")
        elif sprachetable.iloc[items]["S903_Sprachkn"] =="ENG":
            eng.append(sprachetable.iloc[items]["S903_Text"])
            #messageFile.write(sprachetable.iloc[items]["S903_Text"] + ",")
            enfile.write('msgstr "%s"' % sprachetable.iloc[items]["S903_Text"] + '\n')
        elif sprachetable.iloc[items]["S903_Sprachkn"] == "sp1":
            sp.append(sprachetable.iloc[items]["S903_Text"])
            #messageFile.write(sprachetable.iloc[items]["S903_Text"] + ",")
        elif sprachetable.iloc[items]["S903_Sprachkn"] =="PT":
            pt.append(sprachetable.iloc[items]["S903_Text"])
            #messageFile.write(sprachetable.iloc[items]["S903_Text"] + ",")
            ptfile.write('msgstr "%s"' % sprachetable.iloc[items]["S903_Text"] + '\n')
    #messageFile.write('\n')
#messageFile.close()
enfile.close()
ptfile.close()
#data=[deu,eng,pt,sp]
#print(data)
#print(eng)
#print(deu)
#print(sp)
#print(pt)

#print(len(eng),len(deu),len(pt))
#print(len(sp))
#cols = ['DE', 'ENG', 'PT', 'SP1']
df1 = pd.DataFrame(
    {'DEU': pd.Series(deu),
    'EN': pd.Series(eng),
     'PT': pd.Series(pt)
   })

print(df1.head(n=100))










