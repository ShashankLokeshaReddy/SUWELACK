USE [ksmaster]
GO
 
/****** Object:  UserDefinedFunction [dbo].[kstf_TA55LastBookFB1]    Script Date: 06.04.2022 11:13:11 ******/
DROP FUNCTION [dbo].[kstf_TA55LastBookFB1]
GO
 
/****** Object:  UserDefinedFunction [dbo].[kstf_TA55LastBookFB1]    Script Date: 06.04.2022 11:13:11 ******/
SET ANSI_NULLS ON
GO
 
SET QUOTED_IDENTIFIER ON
GO
 
-- ==========================================================================================
-- Author:        Detlef Gruhl
-- Create date: 30.01.2014
-- Description:    Letzten Buchungstimestamp ermitteln
-- 23.10.2020 Umstellung auf TA51_FB1
-- ==========================================================================================
CREATE FUNCTION [dbo].[kstf_TA55LastBookFB1]
(    
    -- Add the parameters for the function here
    @FirmaNr varchar(2)
    ,@PersNr as BigInt
    ,@Platz as varchar(20)
 
)
RETURNS TABLE 
AS
RETURN 
(
select DatumTS,TagId,Herkunft 
from (Select Top 1 TA55_EndeTS as DatumTS,TA55_TagId as TagId,'TA55' as Herkunft from KSAlias.dbo.TA55_FAB1
        where TA55_FirmaNr = @FirmaNr
            and TA55_Platz_Ist = @Platz
            order by TA55_EndeTS desc
            union
        Select Top 1 TA51_EndeTS as DatumTS,TA51_TagId as TagId,'TA51' as Herkunft from KSAlias.dbo.TA51_FAB1
            where TA51_FirmaNr = @FirmaNr
            and TA51_Platz_Ist = @Platz
            and TA51_Belegnr not in ('GK1')
            and TA51_BuArt in ('P')
            order by TA51_EndeTS desc
        union
        Select min(T951_DatumTS) as DatumTS, T951_TagId as TagId,'T951' as Herkunft from KSAlias.dbo.T951_Buchungsdaten 
        inner join (
                    -- letzte Buchungen an dem Tag am Arbeitsplatz
                    Select T951_FirmaNr as FirmaNr, T951_PersNr as PersNr,max(T951_DatumTS) as TS from KSAlias.dbo.T951_Buchungsdaten 
                    inner join (
                            -- TagId der buchenden Person
                            select T951_FirmaNr as xFA,T951_PersNr as xPNr,max(T951_TagId ) as xTId
                                from KSAlias.dbo.T951_Buchungsdaten where T951_FirmaNr = @FirmaNr and T951_PersNr = @PersNr
                                group by T951_FirmaNr ,T951_PersNr 
                                ) as a on T951_FirmaNr  = xFA and T951_TagId = xTId and T951_ArbIst = @Platz
                    group by T951_FirmaNr,T951_PersNr
                    ) as b on T951_FirmaNr = FirmaNr and T951_PersNr = PersNr and T951_DatumTS=TS and T951_Satzart in ('A','K')
        group by T951_FirmaNr,T951_TagId
 
     ) as x
 
)
GO