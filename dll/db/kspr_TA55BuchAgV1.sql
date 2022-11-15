USE [ksmaster]
GO

drop PROCEDURE kspr_TA55BuchAgV1
go

-- ===========================================================================================================
-- Author:		Detlef Gruhl
-- Create date: 20.02.2013
-- Description:	TA55 Buchung mit RÅckmeldeart = 7
-- Anfang = Ende
-- PrÅfen davorliegender Arbeitsgang, Platz und beenden
-- FiniAgVor - 1=TA22_Typ = 7 buchen, 2=SammelauftrÑge buchen
-- 19.09.2018 - Gruppenbuchung nur dann, wenn mit FA_Nr gebucht wurde (bei Belegnummer nur Einzelbuchung!
-- 03.12.2019 Charge
-- 28.09.2020 SetStatusBelegNr mit Terminal  und user-Parameter fÅr Logging bei Fehler
-- 20.07.2021 - Val1-Val5
-- 21.07.2022 - umbenannt in V1 (Trennung alte-neue Version!)
-- ===========================================================================================================
CREATE PROCEDURE [dbo].[kspr_TA55BuchAgV1]
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
   ,@Herkunft varchar(2)
   ,@FiniAGVor int -- 0 = nur aktuelle Folge beenden,1=davorliegende Arbeitsfolgen (gleicher und abw. Platz beenden),2=nur davorliegende Folgen mit gleichem Platz beenden
   ,@Gen_Stat varchar(2)
   ,@Auf_Stat varchar(2)
   ,@User varchar(3)
   ,@ScanFA integer
 AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;
	

	declare  @xPlatz_Soll varchar(20) --Soll-Platz des aktuellen Beleges
	declare @xTA06FirmaNr varchar(2)
	declare @xTA06FANr varchar(20)
	declare @xTA06FAAgNr varchar(4)
	declare @xTA06FASort varchar(2)
	declare @xTA06BelegNr varchar(30)
	declare @xTA06PlatzSoll varchar(20)
	declare @xTA06AufStat varchar(2)

	declare @ErrMsg as varchar(4000)
    declare @ErrNb as varchar(50)
    declare @Trace as varchar(256)
    
    declare @xFiniAgVor int --1 = davorliegenden Arbeitsplatz beenden
    declare @xbEnd int
    declare @xts datetime
    declare @Grp int -- RÅckgabe mu· @Grp sein!!!
    declare @xGrpRet int
    
    declare @xJobId varchar(30)
	declare @xT905_Art varchar(5) --16.09.2015 - Parametrieren letzter Ag = '3' = beennden!!!
	
 
    
    set @xFiniAgVor = 1
    set @xts = dbo.ksfc_GetTimeStamp()
    set @xJobId = dbo.ksfc_GetTime(@xts)
    
    exec dbo.kspr_S995Terminal @FirmaNr,'ADM',@Terminal,'TRM','TA55BuchAg',@BelegNr,'TA55Insert'  ,'ADM',@xJobId
    
	-- Habaspezial exec dbo.kspr_SIdxStatistik


--	print 'update'


    --19.10.2015 where Auf_stat eingefÅgt - SammelauftrÑge beenden funktioniert sonst nicht!
   if exists ( Select * from KSAlias.dbo.TA55_FAB1 where TA55_FirmaNr = @FirmaNr and TA55_DatumTS = @DatumTS and TA55_Platz_Ist = @Platz_Ist and TA55_Auf_Stat <'20') 
   begin
		-- Auftrag beenden
		Update KSAlias.dbo.TA55_FAB1 set TA55_Auf_Stat = @Auf_Stat,TA55_EndeTS = @EndeTS 
			,TA55_MengeGut = TA55_MengeGut + @MengeGut  
			,TA55_MengeAus = TA55_MengeAus + @MengeAus 
			,TA55_Wert1 = TA55_Wert1 + @Val1
			,TA55_Wert2 = TA55_Wert2 + @Val2
			,TA55_Wert3 = TA55_Wert3 + @Val3
			,TA55_Wert4 = TA55_Wert4 + @Val4
			,TA55_Wert5 = TA55_Wert5 + @Val5
			,TA55_UA51ID = @UA51ID 
			,TA55_Aenderung = @xTS 
			
			from KSAlias.dbo.TA55_FAB1
			inner join KSAlias.dbo.T905_ArbMasch   on T905_FirmaNr = TA55_FirmaNr and T905_Nr = TA55_Platz_ist
			where TA55_FirmaNR = @FirmaNr 
					and TA55_DatumTS = @DatumTS
					and TA55_BelegNr = @BelegNr 
					and T905_Nr = @Platz_ist
   end
   else
   begin
		-- Buchen aktuellen Arbeitsgang
		print 'insert TA55 ' + @BelegNr + ' charge:' + @charge
		exec dbo.kspr_TA55InsertV1 @FirmaNr,@DatumTS,@FA_Nr,@FA_AgNr,@FA_Sort,@BelegNr,@Platz_Ist,@PersNr,@AE,@TagId,@Status,@EndeTS
		,@MengeGut,@MengeAus,@Terminal,@PersNrEnd,@UA51Id,@TE,@TRMan,@TA11Nr,@Charge,@Val1,@Val2,@Val3,@Val4,@Val5,@Gen_Stat,@Auf_Stat,@User,@ScanFA
   end


	-- print @status
	
   
  -- print 'fehllerlele'



    
    exec dbo.kspr_S995Terminal @FirmaNr,'ADM',@Terminal,'TRM','TA55BuchAg',@BelegNr,'TA50Insert'  ,'ADM',@xJobId
	-- 06.07.2017 -- Fehler bei anlegen ignorieren, wenn Auftrag schon begonnen wurde und dies eine Endmeldung ist
	begin try
		 exec dbo.kspr_TA50Insert @FirmaNr,@DatumTS,@BelegNr,0,@PersNr,@TagId,'',@MengeGut,@MengeAus,'',@Auf_Stat,0,0,0,null,0,'',''
		,@Platz_Ist,0,0,0,@Terminal,@UA51Id,@Herkunft,@TRMan,@TA11Nr,@Charge,@xts,@xts,@User,@ScanFA
	end try
	begin catch

	end catch
   

  -- print 'setstatus'

    exec dbo.kspr_S995Terminal @FirmaNr,'ADM',@Terminal,'TRM','TA55BuchAg',@BelegNr,'StatusBelegNr'  ,'ADM',@xJobId
    exec dbo.kspr_TA06SetStatusBelegNr @FirmaNr,@DatumTS,@PersNr,@BelegNr,@Auf_Stat,@Platz_Ist,@Terminal,@User
    

	--print 'updatemenge'


    exec dbo.kspr_S995Terminal @FirmaNr,'ADM',@Terminal,'TRM','TA55BuchAg',@BelegNr,'Update Menge'  ,'ADM',@xJobId
    exec dbo.kspr_TA06UpdateMenge @FirmaNr,@BelegNr,@MengeGut,@MengeAus
    
    -- PrÅfen, ob Gruppenbuchung vorliegt und Gruppe in TA06 buchen (fertigmelden)
	-- 19.09.2018 - nur wenn mit Scan FA gebucht wurde als Gruppenbuchung!
	--print 'ta06'
		exec dbo.kspr_S995Terminal @FirmaNr,'ADM',@Terminal,'TRM','TA55BuchAg',@BelegNr,'Gruppenbuchung Start'  ,'ADM',@xJobId
		exec dbo.kspr_TA55BuchT909TA06 @FirmaNr,@DatumTS,@FA_Nr,@BelegNr,@Platz_Ist,@PersNr,@AE,@TagId,@Status,@EndeTS
		,@MengeGut,@MengeAus,@Terminal,@PersNrEnd,@UA51Id,@Gen_Stat,@Auf_Stat,@User,@ScanFA ,@Grp=@xGrpRet Output

    
    exec dbo.kspr_S995Terminal @FirmaNr,'ADM',@Terminal,'TRM','TA55BuchAg',@BelegNr,'Gruppenbuchung End'  ,'ADM',@xJobId 
   -- Gruppenbuchung! Davorliegende PlÑtze nicht beenden!!!
 --  print cast(@xGrpRet as varchar(10))
   
 --  print 'grpret'

   -- Wenn Gruppenbuchung, dann nicht weiter !!!!!
   if @xGrpRet = 1 return
   if @FiniAGVor = 0 return --keine davor liegenden PlÑtze beenden


  -- print 'nix weite'



   --Platz Soll des aktuellen Beleges suchen.
   -- INFO: Falls PlatzIst abweichend von Soll mu· mit Soll der Folgeplatz geprÅft werden!
    select @xPlatz_Soll=TA06_Platz_Soll ,@xT905_Art = T905_Art
			from KSAlias.dbo.TA06_FAD1  
			inner join KSAlias.dbo.T905_ArbMasch  on T905_FirmaNr = TA06_FirmaNr and T905_Nr = TA06_Platz_Soll
			where TA06_FirmaNr = @FirmaNr and TA06_BelegNr = @BelegNr
			
	if @xPlatz_Soll is null 
	begin
		set @xPlatz_Soll = @Platz_Ist
	 end
	else
	begin
	--18.09.2016 and @FiniAGVor = 1)
		if not @xT905_Art = '3' set @xFiniAgVor = 0 --16.09.2015 davorliegende ArbeitsplÑtze mit Menge 0 beenden
	end

			
			
			
    -- PrÅfen, ob der letzte Arbeitsgang am gleichen Platz
   
    select  Top 1 @xTA06FirmaNr = TA06_FirmaNr,@xTA06BelegNr =TA06_BelegNr,@xTA06PlatzSoll =TA06_Platz_Soll 
			from KSAlias.dbo.TA06_FAD1 
			where TA06_FirmaNr = @FirmaNr and TA06_FA_Nr = @FA_Nr and TA06_FA_AgNr > @FA_AgNr
			order by TA06_FA_Nr,TA06_FA_AgNr,TA06_FA_Sort

 --print 'fehler'
 
	if @xTA06PlatzSoll is not null
	begin
		if @xTA06PlatzSoll = @xPlatz_Soll
		begin
			set @xFiniAgVor =0 --nicht der letzte Arbeitsplatz
		end
	end
	
	
	if @xFiniAGVor = 0 return --keine davor liegenden PlÑtze beenden
    
   
     exec dbo.kspr_S995Terminal @FirmaNr,'ADM',@Terminal,'TRM','TA55BuchAg',@BelegNr,'Check last Ag'  ,'ADM',@xJobId
    -- RÅckwÑrts ab Arbeitsgang lesen
    declare tmpTabTA06 CURSOR FOR
	select  TA06_FirmaNr,TA06_FA_Nr,TA06_FA_AgNr,TA06_FA_Sort,TA06_BelegNr,TA06_Platz_Soll,TA06_Auf_Stat 
			from KSAlias.dbo.TA06_FAD1  
			where TA06_FirmaNr = @FirmaNr and TA06_FA_Nr = @FA_Nr and TA06_FA_AgNr < @FA_AgNr
			order by TA06_FA_Nr,TA06_FA_AgNr desc ,TA06_FA_Sort desc

	open tmpTabTA06

	--print 'fetch'

	FETCH next from tmpTabTA06  INTO 
				@xTA06FirmaNr,@xTA06FANr,@xTA06FAAgNr,@xTA06FASort,@xTA06BelegNr,@xTA06PlatzSoll,@xTA06AufStat
		set @xbEnd = @@FETCH_STATUS
			--print 'Fetch' + cast(@@FETCH_STATUS as varchar(5))
		WHILE @xbEnd = 0  
		BEGIN
			BEGIN TRY
			--DEBUG print @xTA06BelegNr + ' - ' + @xTA06PlatzSoll + ' -- ' +  @xPlatz_Soll
				-- gleicher Platz andere Lohngruppe
				-- keine Buchung in TA55!
				--print @xTA06BelegNr + '  ' + @xTA06FAAgNr
				exec dbo.kspr_S995Terminal @FirmaNr,'ADM',@Terminal,'TRM','TA55BuchAg',@BelegNr,@xTA06BelegNr  ,'ADM',@xJobId
				if @xTA06PlatzSoll = @xPlatz_Soll
				begin
					--if @xTA06AufStat = '0' 
					--begin
						set @Trace = 'PlatzSoll = Ist - TA55'
						/*
						exec dbo.kspr_TA55Insert @FirmaNr,@DatumTS,@xTA06FANr,@xTA06FAAgNr,@xTA06FASort,@xTA06BelegNr,@Platz_Ist,@PersNr,@AE,@TagId,@Status,@EndeTS
							,@MengeGut,@MengeAus,@Terminal,@PersNrEnd,@UA51Id,@Gen_Stat,@Auf_Stat,@User
						*/
						exec dbo.kspr_TA50Insert @FirmaNr,@DatumTS,@xTA06BelegNr,'0',@PersNr,@TagId,'',@MengeGut,@MengeAus,'',@Auf_Stat,0,0,0,null,0,'',''
							,@Platz_Ist,0,0,0,@Terminal,@UA51Id,'AU',0,'','',@xts,@xts,@User,0
						
						set @Trace ='PlatzSoll = Ist - TA06'
						exec dbo.kspr_TA06SetStatusBelegNr @FirmaNr,@DatumTS,@PersNr,@xTA06BelegNr,@Auf_Stat,@Platz_Ist,@Terminal,@User
						exec dbo.kspr_TA06UpdateMenge @FirmaNr,@xTA06BelegNr,@MengeGut,@MengeAus
					--end
				end
				else
				-- 1. davorliegender abweichende Arbeitsplatz 
				-- automatisch mit Menge 0 beenden
				-- EinschrÑnkung Status?
				begin
					-- war der letzte, beenden
					if @xFiniAgVor =1 and @FiniAGVor in (1)
					begin
						-- davorliegende beenden, wenn abweichend und der aktuelle AG beendet wird
						if @Auf_Stat in ('30','31','3')
						begin
							
							set @Trace = 'PlatzSoll <> Ist - TA55'
							/*
							--keiner Person zuzuordnen - nur Arbeitsgang registrieren
							exec dbo.kspr_TA55Insert @FirmaNr,@DatumTS,@xTA06FANr,@xTA06FAAgNr,@xTA06FASort,@xTA06BelegNr,@Platz_Ist,@PersNr,@AE,@TagId,@Status,@EndeTS
								,0,0,@Terminal,@PersNrEnd,0,@Gen_Stat,@Auf_Stat,@User
								*/
							exec dbo.kspr_TA50Insert @FirmaNr,@DatumTS,@xTA06BelegNr,'0',@PersNr,@TagId,'',@MengeGut,@MengeAus,'',@Auf_Stat,0,0,0,null,0,'',''
							,@Platz_Ist,0,0,0,@Terminal,@UA51Id,'AU',0,'','',@xts,@xts,@User,0

															
							set @Trace = 'PlatzSoll <> Ist - TA06'
							 exec dbo.kspr_TA06SetStatusBelegNr @FirmaNr,@DatumTS,@PersNr,@xTA06BelegNr,@Auf_Stat,@xTA06PlatzSoll,@Terminal,@User
						end
					end
					
					
				end
			
			
			
			END TRY
			BEGIN CATCH
				Select @ErrNb = ERROR_NUMBER() 
				Select   @ErrMsg = Error_Message() 
				 Print 'Error in kspr_TA55BuchAg ' + @Trace + ' ' + @ErrNb + ' ' + @ErrMsg + ' in Beleg:' + @BelegNr + ' Platz:' + @Platz_Ist
			END CATCH
			

			if @xbEnd = 0 
			begin
				FETCH next from tmpTabTA06  INTO 
				@xTA06FirmaNr,@xTA06FANr,@xTA06FAAgNr,@xTA06FASort,@xTA06BelegNr,@xTA06PlatzSoll,@xTA06AufStat
			
				set @xbEnd = @@FETCH_STATUS
			end
					
			
				
		END
	exec dbo.kspr_S995Terminal @FirmaNr,'ADM',@Terminal,'TRM','TA55BuchAg',@BelegNr,'End last Ag'  ,'ADM',@xJobId
	
	CLOSE tmpTabTA06
	DEALLOCATE tmpTabTA06
		
 
    
END


go
