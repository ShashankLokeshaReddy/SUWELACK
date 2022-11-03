USE [ksmaster]
GO
 
/****** Object:  UserDefinedFunction [dbo].[kstf_TA06FAPlatz]    Script Date: 06.04.2022 11:12:04 ******/
DROP FUNCTION [dbo].[kstf_TA06FAPlatz]
GO
 
/****** Object:  UserDefinedFunction [dbo].[kstf_TA06FAPlatz]    Script Date: 06.04.2022 11:12:04 ******/
SET ANSI_NULLS ON
GO
 
SET QUOTED_IDENTIFIER ON
GO
 
-- ==========================================================================================
-- Author:        Detlef Gruhl
-- Create date: 01.10.2020
-- Description:    TA06 FA/Platz liefern (Aufruf vom Terminal
-- ==========================================================================================
CREATE FUNCTION [dbo].[kstf_TA06FAPlatz]
(    
    -- Add the parameters for the function here
    @FirmaNr varchar(2)
    ,@Platz varchar(20)
    ,@FANr varchar(36)

)
RETURNS TABLE 
AS
RETURN 
(
    Select  a.TA06_FirmaNr,TA06_FA_Nr,TA06_FA_AgNr,TA06_FA_Sort,a.TA06_BelegNr,TA06_FA_Art,TA06_AgBez,TA06_ErpNr,TA06_Platz_Soll,a.TA06_Platz_ist,TA06_RueckArt
    ,TA06_ArtikelNr
    ,Ta06_MeEinheit,TA06_MeFaktor,TA06_Soll_Me,TA06_Ist_Me,TA06_Ist_Me_Gut ,TA06_Ist_Me_Aus 
    ,TA06_TE,TA06_TE1,TA06_TE_Soll,TA06_TR,TA06_TR1
    ,TA06_TEZB,TA06_TRZB
    ,TA06_TE2,TA06_TE2ZB,TA06_TE2_Soll
    ,TA06_PrKn1,TA06_PrKn2
    ,TA06_ErpNr1,TA06_ErpNr2
    ,TA06_TrGrWechsel,TA06_MatBuch
    ,TA06_LagerPlatz,TA06_WagenNr,TA06_LohnGrp
    ,TA06_Freigabe,TA06_Auf_Stat,TA06_Sys_Stat
    ,TA21_Nr,TA21_Bez,TA21_Typ,TA21_StartAgain ,TA21_Global,TA21_Show,TA21_Export
    ,TA22_Nr,TA22_Typ,TA22_MengeBuch ,TA22_MengeBuchSec,TA22_MengeBuchSecU,TA22_Menge,TA22_Dialog,TA22_Dauer,TA22_FAEnde,TA22_MengeVorb,TA22_ShowTR,TA22_ShowTA11
    ,TA22_IstMeGes,TA22_IstMeSollWarn,TA22_ShowCancelBtn ,TA22_ShowCharge,TA22_AddMenge 
    ,TA05_Kd_AufNR
    ,TA20_Nr,TA20_Bez
         from KSAlias.dbo.TA06_FAD2 as a
        inner join KSAlias.dbo.TA06_FAD3 as b on a.TA06_FirmaNR  =@FirmaNr and b.TA06_FirmaNr =a.TA06_FirmaNr and b.TA06_BelegNr = a.TA06_BelegNr and  TA06_Platz_Soll = @Platz  and  TA06_FA_NR = @FANr
        inner join KSAlias.dbo.ta05_fak1 on ta05_firmanr = a.ta06_firmanr and ta05_fa_nr = a.ta06_fa_nr
        inner join KSAlias.dbo.t905_ArbMasch on t905_firmanr = a.ta06_firmanr and T905_Nr = a.TA06_Platz_Soll
        inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr = a.TA06_FirmaNr and TA21_Nr = TA06_FA_Art 
        inner join KSAlias.dbo.TA22_AuRueck  on TA22_FirmaNr = a.TA06_FirmaNr and TA22_Nr = a.TA06_RueckArt 
        inner join KSAlias.dbo.ta20_artikel on ta20_firmanr = a.ta06_firmanr and ta20_nr = ta06_artikelnr --hier war left join !
 
           


)
GO