USE [ksmaster]
GO
 
/****** Object:  StoredProcedure [dbo].[kspr_TA51UpdateFAEndGKFB1]    Script Date: 06.04.2022 11:08:37 ******/
DROP PROCEDURE [dbo].[kspr_TA51UpdateFAEndGKFB1]
GO
 
/****** Object:  StoredProcedure [dbo].[kspr_TA51UpdateFAEndGKFB1]    Script Date: 06.04.2022 11:08:37 ******/
SET ANSI_NULLS ON
GO
 
SET QUOTED_IDENTIFIER ON
GO
 

-- ==========================================================================================
-- Author:        Detlef Gruhl
-- Create date: 17.10.2012
-- Description:    Aufträge automatisch bei Wechselbuchung unterbrechen
-- ==========================================================================================
Create PROCEDURE [dbo].[kspr_TA51UpdateFAEndGKFB1] 
     @FirmaNr varchar(2)
    , @EndeTS datetime
    , @PersNr bigint
    , @notPlatz varchar(20)
    , @User varchar(3)
    , @Terminal varchar(100)
AS
BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON;
    declare @TS datetime
    declare @TagId datetime

    set @TS =  dbo.ksfc_GetTimeStamp()
    set @Tagid = dbo.ksfc_GetDate(@TS)
 
    -- Log schreiben
    insert into KSAlias.dbo.TA50_faerfassung (TA50_Firmanr,TA50_datumts,TA50_Belegnr,TA50_Ruecknr,TA50_PersNr,TA50_TAGID,TA50_Zusart,TA50_MengeIstGut,TA50_MengeIstAus,TA50_Satzart,TA50_Auf_Stat,Ta50_StatusRef,
                    TA50_StatusAuto,TA50_Status,TA50_JobBegin,TA50_Herkunft,TA50_Anlage,TA50_Aenderung,TA50_User,TA50_Zuschlag,TA50_Entlohnung,TA50_Zeitart,
                    TA50_Platz_Ist,TA50_Dauer,TA50_SB,TA50_Refid,TA50_Terminal) 
                Select TA51_FirmaNr, @EndeTS ,TA51_Belegnr,'',@PERSNR,@TagId,'',0,0,'A','25',0,
                        0,0,@TS,'WB',@TS,@TS,@User,'',T910_Entlohnung,'',
                        TA51_Platz_Ist,0,@PersNr,0,@Terminal
                        from KSAlias.dbo.TA51_FAB1  
                        inner join KSAlias.dbo.TA06_FAD2  with (nolock) on TA06_FirmaNr = TA51_FirmaNr and TA06_BelegNr= TA51_BelegNr
                        inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr= TA06_FirmaNr and TA21_Nr = TA06_FA_Art
                        inner join KSAlias.dbo.T910_Personalliste on T910_FirmaNr = TA51_FirmaNr and T910_Nr = TA51_PersNr 
                        where  TA51_FirmaNr = @FirmaNr  
                            and (TA51_Auf_Stat = '10' or TA51_Auf_Stat = '11')
                            and TA51_BuArt = 'P'
                            and TA51_PersNr = @PERSNR
                            and TA51_Platz_Ist <> @notPlatz
                            and (TA21_Typ = '3' )

                        group by
                            TA51_FirmaNr, TA51_Belegnr,TA51_Platz_Ist,T910_Entlohnung


    -- TA51 Ende setzen                
    update KSAlias.dbo.TA51_FAB1 set TA51_Auf_Stat = '25'
        ,TA51_EndeTS = @EndeTS
         ,TA51_Status = 'UE'
         ,TA51_Gen_Stat    = 0
         ,TA51_Aenderung = @TS
         ,TA51_User = @User
         from KSAlias.dbo.TA51_FAB1
        inner join KSAlias.dbo.TA06_FAD2   on TA06_FirmaNr = TA51_FirmaNr and TA06_BelegNr= TA51_BelegNr
        inner join KSAlias.dbo.TA21_AuArt on TA21_FirmaNr= TA06_FirmaNr and TA21_Nr = TA06_FA_Art
        inner join KSAlias.dbo.T910_Personalliste on T910_FirmaNr = TA51_FirmaNr and T910_Nr = TA51_PersNr 
        where  TA51_FirmaNr = @FirmaNr  
            and (TA51_Auf_Stat = '10' or TA51_Auf_Stat = '11')
            and TA51_BuArt = 'P'
            and TA51_PersNr = @PERSNR
            and TA51_Platz_Ist <> @notPlatz
            and (TA21_Typ = '3' ) 

END
 

GO