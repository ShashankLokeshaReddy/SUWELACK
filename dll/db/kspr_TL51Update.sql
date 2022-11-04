drop PROCEDURE kspr_TL51Update
go

-- =============================================
-- Author:		Detlef Gruhl
-- Create date: 21.01.2015
-- Description:	TL51 MDE- Stîrung beenden
-- Der zu beendende Satz wird automatisch gesucht - Anfang = Ende
-- =============================================
CREATE PROCEDURE [dbo].[kspr_TL51Update]
	@FirmaNr varchar(2)
	,@Platz varchar(20)
	,@EndeTS datetime --Ende Timestamp
	,@Terminal varchar(20)
	,@User varchar(20)
	,@FiniNotRuest int --nur beenden, wenn <> Ruest 0-RÅst-GK wird beendet, 1-nur wenn <>RuestGK wird beendet 
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;
	
	declare @xTagId datetime
	declare @xBelegNr varchar(30)
	declare @xTS datetime
	declare @xAufStat varchar(3)
	declare @xPersnr bigint
	declare @xTA05AufArt varchar(2)
		
	declare @xFANr varchar(30)
	declare @xFAAgNr varchar(4)
	declare @xFASort varchar(1)
	declare @xFARuest varchar(30)

	
	set @xFARuest = dbo.ksfc_T900GetValue(@FirmaNr,'MDEGK_Ruest') + '%' --definierter FA fÅr RÅsten

	if @FiniNotRuest = 0
	begin
		-- letzten gebuchte RÅst-GK mit Ende=Anfang - Endezeitpunkt setzen
		Update  [KSAlias].dbo.TL51_MaStop  set TL51_EndeTS = @EndeTS,TL51_Dauer = datediff(second,TS,@EndeTS)
				,TL51_Aenderung=dbo.ksfc_GetTimestamp()
				,TL51_User = @User
		from [KSAlias].dbo.TL51_MaStop
		inner join (select TL51_FirmaNr as FirmaNr,TL51_Platz as Platz,max(TL51_AnfangTS) as TS  from  [KSAlias].dbo.TL51_MaStop
				where TL51_FirmaNr = @FirmaNr and TL51_Platz = @Platz 
				group by TL51_FirmaNr,TL51_Platz 
				) as a on TL51_FirmaNr = FirmaNr and TL51_Platz = Platz and TL51_AnfangTS = TS and TL51_AnfangTS = TL51_EndeTS  and TL51_BelegNr like @xFARuest
	end
	else
	begin
		Update  [KSAlias].dbo.TL51_MaStop  set TL51_EndeTS = @EndeTS,TL51_Dauer = datediff(second,TS,@EndeTS)
						,TL51_Aenderung=dbo.ksfc_GetTimestamp()
						,TL51_User = @User
				from [KSAlias].dbo.TL51_MaStop
				inner join (select TL51_FirmaNr as FirmaNr,TL51_Platz as Platz,max(TL51_AnfangTS) as TS  from  [KSAlias].dbo.TL51_MaStop
						where TL51_FirmaNr = @FirmaNr and TL51_Platz = @Platz 
						group by TL51_FirmaNr,TL51_Platz 
						) as a on TL51_FirmaNr = FirmaNr and TL51_Platz = Platz and TL51_AnfangTS = TS and  TL51_AnfangTS = TL51_EndeTS  and TL51_BelegNr not like @xFARuest

	
	end



/*
	Select Top 1 @xTagId = T951_TagId ,@xPersNr = T951_persNr from dbo.kstf_T951AktPerson (@FirmaNr,@Platz) order by T951_DatumTS desc

	Select @xBelegNr = TA55_BelegNr,@xTS=TA55_DatumTS,@xAufStat = TA55_Auf_Stat,@xTA05AufArt = TA05_AufArt 
		,@xTagId = TA55_TagId,@xFANr = TA55_FA_Nr,@xFASort = TA55_FA_sort 
	 from dbo.kstf_TA55LastFA_1(@FirmaNr,@Platz) --letzter gebuchter auftrag vor GK-Stîrung
	
	-- Der Auftrag vor der Stîrung lÑuft noch
	-- laufenden Auftrag beenden
	if @xAufStat in ('10','11') and @xTA05AufArt in ('10','11')
	begin
		update [$(KSAlias)].dbo.TA55_FAB1 set TA55_Auf_Stat = '21'
				, TA55_EndeTS = @EndeTS 
				, TA55_Aenderung = dbo.ksfc_GettimeStamp() 
			 where TA55_FirmaNr = @FirmaNr and TA55_DatumTS = @xTS and TA55_Platz_Ist = @Platz

		
		
		-- letzter gebuchter Auftrag = Stîrung beenden und den davor wieder anfangen
		exec dbo.kspr_TA55Ende @FirmaNr,@xTS,@xFANr ,@xFAAgNr ,@xFASort ,@xBelegNr ,@Platz,@xPersNr,'',@xTagId,'UE',@EndeTS,0,0,@Terminal,@xPersNr,0,'0'

	end
	

*/

	


		

   





END
go
