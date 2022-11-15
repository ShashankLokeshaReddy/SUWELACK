USE [ksmaster]
GO

drop PROCEDURE kspr_TA55InsertV1
go
-- =============================================
-- Author:		Detlef Gruhl
-- Create date: 20.02.2013
-- Description:	TA55 anlegen
-- 03.12.2019 Charge
-- 20.04.2022 AnzFA,Bem 
-- 21.07.2022 Umbenannt in V1
-- =============================================
Create PROCEDURE [dbo].[kspr_TA55InsertV1] 
	@FirmaNr varchar(2)
   ,@DatumTS datetime
   ,@FA_Nr varchar(40)
   ,@FA_AgNr varchar(4)
   ,@FA_Sort varchar(2)
   ,@BelegNr varchar(46)
   ,@Platz_Ist varchar(20)
   ,@PersNr numeric(10,0)
   ,@AE varchar(2)
   ,@TagId datetime
   ,@Status varchar(2)
   ,@EndeTS datetime
   ,@MengeGut numeric(10,3)
   ,@MengeAus numeric(10,3)
   ,@Terminal varchar(100)
   ,@PersNrEnd numeric(10,0)
   ,@UA51ID bigint
   ,@TE float
   ,@TRMan float
   ,@TA11Nr varchar(10)
   ,@Charge varchar(10) 
   ,@Val1 numeric(10,3)
   ,@Val2 numeric(10,3)
   ,@Val3 numeric(10,3)
   ,@Val4 numeric(10,3)
   ,@Val5 numeric(10,3)
   ,@Gen_Stat varchar(2)
   ,@Auf_Stat varchar(2)
   ,@User varchar(3)
   ,@ScanFA integer
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;
	Declare @xRefId bigint
	DECLARE @Cnt int
	declare @xTS as datetime
	
	 set @xTS = dbo.ksfc_GetTimeStamp()
	
	

   exec dbo.kspr_Getcounter @FirmaNr,'TA51_REFID', @cnt = @xRefId OUTPUT
	-- Buchungen der TA55 vom Vortag auf den aktuellen Tag anlegen, und den Auftrag vom Vortag beenden
	-- Bei Insert wird der TA51-Buchungssatz der anmeldenden Person angelegt!!!!!
	INSERT INTO KSAlias.dbo.TA55_FAB1 (TA55_FirmaNr,TA55_DatumTS,TA55_FA_Nr,TA55_FA_AgNr,TA55_FA_Sort,TA55_BelegNr,TA55_Lagerplatz ,TA55_Charge
		,TA55_Platz_Ist,TA55_PersNr,TA55_AE,TA55_Auf_Stat,TA55_Anlage,TA55_Aenderung,TA55_User,
		TA55_RefId,TA55_TagId,TA55_Status,TA55_MengeGut,TA55_MengeAus,TA55_TE,TA55_TR,TA55_Terminal,TA55_Gen_Stat,TA55_Sys_Stat,TA55_UA51Id,TA55_EndeTS,TA55_PersNrEnd,TA55_ScanFA
		,TA55_Wert1,TA55_Wert2,TA55_Wert3,TA55_Wert4,TA55_Wert5,TA55_AnzFA,TA55_Bemerkung)
		Values
		(@FirmaNr,@DatumTS,@FA_Nr,@FA_AgNr,@FA_Sort,@BelegNr,@TA11Nr,@Charge,@Platz_Ist,@PersNr,@AE,@Auf_Stat,@xTS,@xTS,@User,@xRefId
			,@TagId,@Status,@MengeGut,@MengeAus,@TE,@TRMan,@Terminal,@Gen_Stat,0,@UA51Id,@EndeTS,@PersNrEnd,@ScanFA
			, @Val1,@Val2,@Val3,@Val4,@Val5,'0',''
		)
END

go
