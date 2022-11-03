drop FUNCTION kstf_TA51MonatGK
go


-- ==========================================================================================
-- Author:		Detlef Gruhl
-- Create date: 02.09.2015
-- Description:	GK Periode Arbeitsplatz 
-- ==========================================================================================
CREATE FUNCTION [dbo].[kstf_TA51MonatGK]
(	
	-- Add the parameters for the function here
	@FirmaNr varchar(2)
	,@DVon as date
	,@DBis as date
)
RETURNS TABLE 
AS
RETURN 

(
	SELECT            TA51_AnfangTS, TA51_PersNr, TA51_BelegNr, TA51_RefNr
                      ,TA51_TagId, TA51_RueckNr, TA51_Zeitart, TA51_ZusArt 
                      ,TA51_Anfang, TA51_EndeTS, TA51_DauerTS, TA51_Ende 
                      ,TA51_Dauer
					  ,TA51_Dauer / 60 as TA51_Dauer_h
					  , TA51_Soll_TE, TA51_Soll_TR, TA51_Soll_Zus
                      ,TA51_MengeIstGut, TA51_MengeIstAus, TA51_Satzart 
                      ,TA51_Auf_Stat, TA51_Status, TA51_JobBegin, TA51_Anlage 
                      ,TA51_Aenderung, TA51_User, TA06_FA_NR, TA06_FA_AgNr 
                      ,TA06_FA_Sort, TA06_FA_Art, TA06_AgBez,TA06_Soll_Me
                      ,TA21_AuArt.TA21_Bez 
                    --  ,TA27_BezT901_Firma.T901_logo, T925_Bez, 
                      TA51_Typ, TA51_ID, TA51_Herkunft, TA51_SB, 
                      TA51_Sys_Stat, TA51_Platz_Ist, TA51_Entlohnung
					  ,TA21_Typ
					  , TA05_KD_AufNr, 
                      TA05_ArtikelBez, TA51_Bemerkung, TA05_ArtikelNr,TA05_PulkNR,
                      TA05_Mass01,TA05_Mass02,TA05_Mass03,TA05_Volumen,TA05_Preis
					  ,T904_FirmaNR, T904_NR, T904_NRExtern 
                      ,T904_Bez, T904_GruppeNr                  
                      ,convert(varchar(6),TA51_TagId,112) AS TA51_Monat
					  ,T910_Nr,T910_Name,T910_Vorname
					  ,T905_Bez
					  ,T901_Logo
					  ,T903_Nr,T903_Bez 
                    
                                         
FROM         
          [KSAlias].dbo.TA51_FABuchung
                      
                      INNER JOIN [KSAlias].dbo.TA06_FAD1 ON TA51_FirmaNR = TA06_FirmaNr AND TA51_BelegNr =TA06_BelegNr 
						and TA51_Tagid >=@DVon and TA51_Tagid <=@DBis   and TA51_Buart='P' 
                      INNER JOIN [KSAlias].dbo.TA05_FAK1 ON TA06_FirmaNr =TA05_FirmaNr AND TA06_FA_NR = TA05_FA_NR 
					  inner  join [KSAlias].dbo.TA21_AuArt  ON TA21_FirmaNR = TA06_FirmaNr AND TA21_Nr = TA06_FA_Art and TA21_Typ in ('3')
                      -- inner JOIN [KSAlias].dbo.TA01_AUK0 on  TA05_FirmaNr = TA01_FirmaNr AND  TA05_KD_AufNr = TA01_KD_AUFNR 
                      inner JOIN [KSAlias].dbo.T905_ArbMasch on T905_FirmaNr = TA51_FirmaNR  and T905_NR =TA51_Platz_Ist 
                      inner join [KSAlias].dbo.T904_Kostenstellen on T904_FirmaNR = T905_FirmaNr and T904_NR = T905_KstNr 
					  inner join [KSAlias].dbo.T903_Gruppen  on T903_FirmaNR = T904_FirmaNr and T903_NR = T904_GruppeNr 
					   inner JOIN [KSAlias].dbo.T910_Personalliste ON T910_FirmaNR = TA51_FirmaNR and T910_Nr = TA51_PersNr                
                      inner JOIN [KSAlias].dbo.T901_Firma ON TA51_FirmaNR = T901_NR 
                  --    LEFT OUTER JOIN [$(KSAlias)].dbo.TA27_Zuschlaege ON TA51_FirmaNR = TA27_FirmaNR AND TA51_ZusArt = TA27_Nr 

        
)
go
