from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
from sqlalchemy import exc

user = 'ksadmin'
password = 'ksadmin'
host = 'HOC-W10-212\SQL19'
DB = 'ksrotpunkt'
driver = 'SQL Server Native Client 11.0'
DATABASE_CONNECTION = f'mssql://{user}:{password}@{host}/{DB}?driver={driver}'
engine = create_engine(DATABASE_CONNECTION)
future_engine = create_engine(DATABASE_CONNECTION, future=True)
connection = engine.connect()

print("db", X998_GrpPlatz, FirmaNr)

def getArbeitplazlist(FirmaNr, X998_GrpPlatz):
    arbeitplatzlist = pd.read_sql_query(text(
        f"""SELECT T905_Nr,T905_bez,T905_Bez2,T905_KstNr,T905_Art,T905_Typ,T905_Akkord,T905_Leist,T905_Freigabe,
        T905_ArbGrNr,T905_Img,T905_StartScreen,T905_Schleuse FROM ksalias.dbo.G905_TermPlatz INNER JOIN 
        ksalias.dbo.T905_ArbMasch ON G905_Platz = T905_nr AND G905_FirmaNr = T905_FirmaNr 
        WHERE G905_FirmaNr = '{FirmaNr}' AND G905_Nr = '{X998_GrpPlatz}' AND T905_Inaktiv <> 1 ORDER BY G905_Lfdnr"""),
        connection)
    return arbeitplatzlist

def getPlazlistGKA(userid, date, FirmaNr):
    persnr = getPersonaldetails(userid)['T910_Nr']
    Platzlist = pd.read_sql_query(text(
        f"""Select T905_Nr, cast(T905_Nr + '________' as varchar(7)) + T905_bez as T905_Bez from T951_Buchungsdaten 
        inner join T905_ArbMasch on T905_FirmaNr = T951_FirmaNr and T905_Nr = T951_Arbist and T951_Satzart in ('K','A')
        and T951_PersNr = {persnr} and T951_TagId = '{date}' where T951_FirmaNr ='{FirmaNr}' group by T905_Nr, T905_Bez"""),
        connection)
    return Platzlist

def getPlazlistFAE(userid, FirmaNr, date):
    persnr = getPersonaldetails(userid)['T910_Nr']
    Platzlist = pd.read_sql_query(text(
        f"""Select T905_Nr, cast(T905_Nr + '________' as varchar(7)) + T905_bez as T905_Bez from T951_Buchungsdaten 
        inner join T905_ArbMasch on T905_FirmaNr = T951_FirmaNr and T905_Nr = T951_Arbist and T951_Satzart in ('K','A')
        and T951_PersNr = {persnr} and T951_TagId = '{date}' where T951_FirmaNr ='{FirmaNr}' group by T905_Nr, T905_Bez"""),
        connection)
    return Platzlist

def getAuftrag(Platz, template, FirmaNr): # TA21_Typ is 3 for GKA and 5 for FA erfassen
    if template == "GK_ändern":
        TA21_Typ = 3
    if template == "FA_erfassen":
        TA21_Typ = 5

    Auftraglist = pd.read_sql_query(text(
        f"""Select TA06_BelegNr,TA06_FA_Nr + '___' + TA06_AgBez as Bez from TA06_FAD2 inner join TA05_FAK1 on 
        TA05_FirmaNr = TA06_FirmaNr and TA05_FA_Nr = TA06_FA_Nr and TA06_Platz_Soll = '{Platz}' and TA06_Auf_Stat < '3'
        inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and TA21_Typ 
        in ('{TA21_Typ}') where TA06_FirmaNr = '{FirmaNr}' group by TA06_BelegNr, TA06_FA_Nr, TA06_AgBez
        order by TA06_BelegNr"""),
        connection)
    return Auftraglist

def getTables_GKA_FAE(userid, Platz, template, FirmaNr):
    persnr = getPersonaldetails(userid)['T910_Nr']
    date = datetime.now().strftime("%Y-%m-%d")
    if template == "GK_ändern":
        tablelist = pd.read_sql_query(text(f"Select * from ksmaster.dbo.kstf_TA51FAAdminFB1('{FirmaNr}', {persnr}, '{date}', '3')"),
        connection)
    if template == "FA_erfassen":
        tablelist = pd.read_sql_query(text(f"Select * from ksmaster.dbo.kstf_TA55FAAdmin('{FirmaNr}', {persnr}, '{date}', '5', '{Platz}')"),
        connection)
    return tablelist

def getArbeitplatzBuchung(FirmaNr, X998_GrpPlatz):
    arbeitplatzlist = pd.read_sql_query(text(
        f"""Select T905_Nr,T905_Bez from T905_ArbMasch inner join G905_TermPlatz on T905_FirmaNr = '{FirmaNr}'  and G905_FirmaNr = T905_FirmaNr and G905_Platz = T905_nr  and G905_Nr = '{X998_GrpPlatz}'"""),
        connection)
    persnr = pd.read_sql_query(
        text(f"""Select * from ksmaster.dbo.kstf_T910G905Bu('{FirmaNr}','{X998_GrpPlatz}')"""),
        connection)
    persnr['T910_Nr'] = persnr['T910_Nr'].astype(int)
    persnr["T910_Name"] = persnr['T910_Name'].astype(str) +" "+ persnr["T910_Vorname"]
    fanr = pd.read_sql_query(text(
        f"""Select TA06_FA_Nr,TA05_ArtikelBez  from TA06_FAD1  inner join TA21_AuArt on TA21_FirmaNr = '{FirmaNr}' and TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and (TA21_Typ in ('3') or  TA06_FA_Art = '02') inner join G905_TermPlatz on G905_FirmaNr = TA06_FirmaNr and G905_Platz = TA06_Platz_soll and G905_Nr = '{X998_GrpPlatz}' inner join TA05_FAK1 on TA05_FirmaNr = TA06_FirmaNr and TA05_FA_Nr = TA06_FA_nr group by TA06_FA_nr,TA05_ArtikelBez  order by TA06_FA_Nr"""),
        connection)
    return [arbeitplatzlist, persnr, fanr]

def getGruppenbuchungGruppe(FirmaNr):
    gruppe = pd.read_sql_query(text(
        f"""Select T903_NR,T903_Bez from T903_Gruppen where T903_FirmaNr = '{FirmaNr}' and T903_GruPrae not in (0)"""),
        connection)
    return gruppe

def getGruppenbuchungFaNr(FirmaNr):
    fanr = pd.read_sql_query(text(
        f"""Select TA05_FA_Nr,TA05_ArtikelBez from TA05_FAK1 where TA05_FirmaNr = '{FirmaNr}' and TA05_FA_Nr like  'GK0%'"""),
        connection)
    return fanr

def getUserID(persnr):
    userid = pd.read_sql_query(text(
        f"""select T912_Nr from ksalias.dbo.T912_PersCard where T912_PersNr = {persnr}"""), 
        connection)
    return round(userid.iloc[0, 0])

def getBelegNr(FA_Nr, Platz, FirmaNr):
    beleg_nr = pd.read_sql_query(text(
        f"""select TA06_BelegNr from dbo.TA06_FAD1  
        inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and TA21_Typ= '3' and TA21_FirmaNR = '{FirmaNr}'
        where TA06_FA_NR = '{FA_Nr}' and TA06_Platz_Soll = '{Platz}' order by TA06_BelegNr"""), connection)
    if beleg_nr.shape[0] == 0:
        return "error"
    return beleg_nr.iloc[0, 0]

def getPersonaldetails(T912_Nr):
    pers_info = pd.read_sql_query(text(
        f"""SELECT T912_Nr,T910_Name,T910_Vorname,T910_Nr FROM ksalias.dbo.T910_Personalliste 
        INNER JOIN ksalias.dbo.T912_PersCard ON T910_Nr = T912_PersNr WHERE T912_Nr = {T912_Nr}"""),
        connection, coerce_float=False)
    pers_info = pers_info.iloc[0, :]  # select first record that matches
    pers_info['T912_Nr'] = str(pers_info['T912_Nr'])
    pers_info['formatted_name'] = pers_info["T910_Vorname"] + ", " + pers_info["T910_Name"]
    return pers_info

def getLastbooking(userid):
    last_booking = pd.read_sql_query(text(
        f"""select top 1 T951_DatumTS, T951_PersNr, T912_Nr, T951_ArbIst
        from T951_bd1 inner join T912_PersCard on T951_BD1.T951_PersNr=T912_PersCard.T912_PersNr
        where T912_Nr='{userid}' order by T951_DatumTS desc"""), connection)
    return last_booking

def getGemeinkosten(userid, FirmaNr):
    last_booking = getLastbooking(userid)
    platz = last_booking.loc[0, "T951_ArbIst"]
    gk_data = pd.read_sql_query(text(
        f"""select top 100 TA05_FA_Nr, TA05_ArtikelBez, TA06_BelegNr, TA06_Platz_Soll from KSAlias.dbo.TA05_FAK1
        inner join KSAlias.dbo.TA06_FAD1 on TA06_FirmaNr = TA05_FirmaNr and TA06_FA_Nr = TA05_FA_Nr and TA06_Platz_Soll = '{platz}'
        inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and TA21_Typ= '3' and TA21_FirmaNR = '{FirmaNr}'
        order by TA06_BelegNr"""), connection)
    return gk_data

def getStatustableitems(userid, FirmaNr):
    persnr = getPersonaldetails(userid)['T910_Nr']
    date = datetime.now().strftime("%Y-%m-%dT00:00:00")
    ts_now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    last_booking = getLastbooking(userid)
    platz = last_booking.loc[0, "T951_ArbIst"]
    upper_items = pd.read_sql_query(text(f"""SELECT * FROM ksmaster.dbo.kstf_T951BD1_Info('{FirmaNr}', {persnr}, '{date}')"""),
                                    connection)
    lower_items = pd.read_sql_query(text(
        f"""SELECT * FROM ksmaster.dbo.kstf_TA55TA51_InfoAllFB1('{FirmaNr}', {persnr}, '{platz}', '{date}', '{ts_now}')"""),
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

def getGroupMembers(GruppeNr, TagId, FirmaNr):
    # e.g. TagId = "2023-01-11T00:00:00"
    # e.g. GruppeNr = "03"
    members = pd.read_sql_query(text(
        f"""Select T905_Nr, T951_PersNr, T905_BuArt from T951_Buchungsdaten
            inner join T905_ArbMasch on T951_FirmaNr='{FirmaNr}' and T905_FirmaNr = T951_FirmaNr
            and T905_Nr = T951_ArbIst and T951_Satzart in ('K', 'A')
            and T951_TagId = '{TagId}' and T905_BuArt in ('3', '1')
            inner join T904_Kostenstellen on T904_FirmaNr = T905_FirmaNr and T904_Nr = T905_KstNr and T904_GruppeNr = '{GruppeNr}'
            group by T905_Nr, T951_PersNr, T905_BuArt"""), connection
    )
    return members

def doGKLoeschen(belegnr, userid, anfangts, FirmaNr):
    persnr = getPersonaldetails(userid)["T910_Nr"]
    with future_engine.connect() as connection:
        ret = connection.execute(text(f"""EXEC ksmaster.dbo.kspr_TA51DeletewLogFB1 @FirmaNr='{FirmaNr}', @TS='{anfangts}', @BelegNr='{belegnr}', @PersNr={persnr}"""))
        connection.commit()
    return ret

def doGKBeenden(userid, FirmaNr):
    persnr = getPersonaldetails(userid)["T910_Nr"]
    with future_engine.connect() as connection:
        try:
            ret= connection.execute(text(f"""EXEC ksmaster.dbo.kspr_TA51GKEnd2FB1 @FirmaNr='{FirmaNr}', @PersNr={persnr}"""))
            connection.commit()
            ret = True
        except exc.SQLAlchemyError as e:
            ret = False           
    return ret

def doFindTS(persnr, dauer, date, FirmaNr):
    userid = getUserID(persnr)
    # date = datetime.now().strftime("%Y-%m-%dT00:00:00")  # day for which new period needs to be found
    platz = getLastbooking(userid).loc[0, "T951_ArbIst"]
    with future_engine.connect() as connection:
        ret = connection.execute(text(f"""EXEC ksmaster.dbo.kspr_TA51FindTSFB1 @FirmaNr='{FirmaNr}', @PersNr={persnr}, @Platz='{platz}', @TagId='{date}', @dauer={dauer}"""))
        rows = ret.cursor.fetchall()
        connection.commit()
    if not rows is None:
        if len(rows) > 1:
            anfang_ts, ende_ts = rows[1]
            return anfang_ts, ende_ts
    return None, None

def doUndoDelete(belegnr, userid, FirmaNr):
    persnr = getPersonaldetails(userid)["T910_Nr"]
    ts = datetime.now().strftime("%Y-%d-%mT%H:%M:%S")
    with future_engine.connect() as connection:
        try:
            ret = connection.execute(text(f"""EXEC ksmaster.dbo.kspr_TA51LogCopyUndoFB1 @FirmaNr='{FirmaNr}', @TS='{ts}', @BelegNr='{belegnr}', @PersNr={persnr}"""))
            connection.commit()
        except:
            return "Auftrag konnte nicht wiederhergestellt werden"
        
def getZaehler(userid, FirmaNr):
    persnr = getPersonaldetails(userid)["T910_Nr"]
    last_booking = getLastbooking(userid)
    platz = last_booking.loc[0, "T951_ArbIst"]
    gk_data = pd.read_sql_query(text(
        f"""SELECT * FROM ksmaster.dbo.kstf_TA06_GKFAGrp('{FirmaNr}', '{platz}', '50', 1)"""), connection)
    return gk_data
