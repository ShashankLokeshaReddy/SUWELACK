USE [ksmaster]
GO
 
/****** Object:  UserDefinedFunction [dbo].[kstf_TA51LastBookFB1]    Script Date: 06.04.2022 11:12:49 ******/
DROP FUNCTION [dbo].[kstf_TA51LastBookFB1]
GO
 
/****** Object:  UserDefinedFunction [dbo].[kstf_TA51LastBookFB1]    Script Date: 06.04.2022 11:12:49 ******/
SET ANSI_NULLS ON
GO
 
SET QUOTED_IDENTIFIER ON
GO
 
 
-- ==========================================================================================
-- Author:        Detlef Gruhl
-- Create date: 30.04.2015
-- Description:    Letzte Buchung T951,TA51 für Ermittlung Anfangszeitpunkt
-- 23.10.2020 Umstellung auf TA%1_FAB1
-- ==========================================================================================
CREATE FUNCTION [dbo].[kstf_TA51LastBookFB1]
(    
    @FirmaNr varchar(2)
    ,@PersNr BigInt
    ,@TS datetime -- aktueller TimeStamp oder Endezeitpunkt (auf Ende buchen und den Anfang suchen
)
RETURNS TABLE 
AS
RETURN 
Select Top 2 * 
 from (Select Top 1 TA51_EndeTS as DatumTS,TA51_Belegnr,TA51_Auf_Stat,'TA51' as Herkunft 
        from KSAlias.dbo.TA51_FAB1
        inner join KSAlias.dbo.TA06_FAD1 on TA06_FirmaNr = TA51_FirmaNr and TA06_BelegNr = TA51_BelegNr
        inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr = TA06_FirmaNr and TA21_Nr = TA06_FA_Art and TA21_Typ not in (8) 
         where TA51_FirmaNr = @FirmaNr and TA51_PersNr = @PersNr and TA51_AnfangTS < @TS and TA51_BuArt in ('P')
         order by TA51_EndeTS desc
         union 
          Select Top 1 T951_DatumTS as DatumTS,'' as TA51_BelegNr,'' as TA51_Auf_Stat,'T951' as Herkunft from  KSAlias.dbo.T951_Buchungsdaten 
          where T951_FirmaNr = @FirmaNr and T951_PersNr = @PersNr and T951_DatumTS < @TS and T951_Satzart in ('A','K')
            order by T951_DatumTS desc 
        ) as x 
 order by DatumTS desc
 
GO