USE [ksmaster]
GO
 
/****** Object:  UserDefinedFunction [dbo].[kstf_TA51FAGKEND]    Script Date: 06.04.2022 11:14:01 ******/
DROP FUNCTION [dbo].[kstf_TA51FAGKEND]
GO
 
/****** Object:  UserDefinedFunction [dbo].[kstf_TA51FAGKEND]    Script Date: 06.04.2022 11:14:01 ******/
SET ANSI_NULLS ON
GO
 
SET QUOTED_IDENTIFIER ON
GO
 
 
-- ==========================================================================================
-- Author:        Detlef Gruhl
-- Create date: 02.09.2015
-- Description:    Auftragsdaten Periode Arbeitsplatz für Kennzahlenermittlung
-- ==========================================================================================
CREATE FUNCTION [dbo].[kstf_TA51FAGKEND]
(    
    -- Add the parameters for the function here
    @FirmaNr varchar(2)
    ,@Persnr as bigint
    ,@Platz as varchar(20)
)
RETURNS TABLE 
AS
RETURN 
 
(
    -- 29.01.2014 - cast in TA51Tagid gesetzt, da plötzlich Probleme in TA60Fill gemacht
    Select TA51_FAB1.*,TA21_Typ,TA21_StartAgain 
    from KSAlias.dbo.TA51_FAB1
    inner join KSAlias.dbo.TA06_FAD2   on TA06_FirmaNr = TA51_FirmaNr and TA06_BelegNr= TA51_BelegNr and TA51_FirmaNr = @FirmaNr 
    inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr= TA06_FirmaNr and TA21_Nr = TA06_FA_Art
    where TA51_PersNr =@Persnr
        and TA51_Auf_stat in ('10','11') 
        and TA51_Buart in ('P')
        and TA51_Platz_ist not in (@Platz)
        and (TA21_Typ not in ('3','8') or TA21_StartAgain ='1')
        or (TA51_Platz_ist not in (@Platz) and TA21_Typ in ('3') and TA51_Auf_Stat in ('10','11') and TA51_BuArt in ('P') and TA51_PersNr =@Persnr )
 
        

)
 
 
 

GO