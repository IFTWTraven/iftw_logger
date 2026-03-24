#ifndef _ELLISYS_ANALYZER_REMOTE_CONTROL_ICE
#define _ELLISYS_ANALYZER_REMOTE_CONTROL_ICE

module Ellisys
{
	module Platform
	{
		module NetworkRemoteControl
		{
			module Analyzer
			{
				exception OperationFailed { string Reason; };
				exception IncorrectState extends OperationFailed { };
				exception UserInteractionPending extends OperationFailed { };
				exception FileSystemError extends OperationFailed { };
				
				const string AnalyzerRemoteControlIdentity = "Ellisys.AnalyzerRemoteControl";
				
				struct AppInfo
				{
					string Id;
					string Description;
					string Version;
					string FileExt;
					bool Interactive;
				};

				struct RecordingStatus
				{
					string DataSource;
					int DurationSeconds;
					long FileSize;
				};
				
				struct TraceFileInfo
				{
					string Path;
					long FileSize;
					long StartDateTimeUtc;
					string SoftwareVersion;
					string DataSource;
					string UniqueId;
					string RecordingOptions;
				};
				
				enum MessageSeverity
				{
					Info	= 1,
					Warning = 2,
					Error	= 3
				};

				enum MarkerColor
				{
					Yellow	= 0,
					Blue	= 1,
					Red		= 2,
					Green	= 3,
					Orange	= 4,
					Purple	= 5
				};

				struct AddMarker
				{
					MarkerColor Color;
					string Text;
				};

				struct GetMarker
				{
					MarkerColor Color;
					string Text;
					long Time;
				};

				struct ExportOption
				{
					string OptionName;
					string OptionValue;
				};

				enum LogicSignalTransitionType
				{
					Any,
					RisingEdge,
					FallingEdge
				};

				struct RunningTask
				{
					string Name;
					int ProgressPercent;
					bool ProgressApplicable;
				};
				
				sequence<long> TimeArray;
				sequence<int> HandleArray;
				sequence<byte> ByteArray;
				sequence<ByteArray> ByteArrays;
				sequence<string> StringArray;
				sequence<GetMarker> GetMarkerArray;
				sequence<ExportOption> ExportOptionArray;
				sequence<RunningTask> RunningTaskArray;
				
				interface AnalyzerRemoteControl
				{
					AppInfo GetAppInfo() throws OperationFailed;
					void ExitApp() throws OperationFailed;

					StringArray GetAvailableDataSources() throws OperationFailed;
					void SelectDataSource(string dataSourceUniqueId) throws OperationFailed;
					string GetSelectedDataSource() throws OperationFailed;

					bool IsRecording() throws OperationFailed;
					RecordingStatus GetRecordingStatus() throws OperationFailed;
					void StartRecording() throws OperationFailed;
					void StopRecordingAndSaveTraceFile(string filename, bool overwrite) throws OperationFailed;
					void AbortRecordingAndDiscardTraceFile() throws OperationFailed;
					string GetRecordingOptions(bool relevantOnly) throws OperationFailed;
					void ConfigureRecordingOptions(string options) throws OperationFailed;
					void InsertMessage(MessageSeverity severity, string message) throws OperationFailed;

					bool IsLoading() throws OperationFailed;
					void StartLoading(string filename) throws OperationFailed;
					TraceFileInfo GetTraceFileInfo() throws OperationFailed;
					void CloseTraceFile() throws OperationFailed;

					bool IsModified() throws OperationFailed;
					void SaveChanges() throws OperationFailed;
					void AddMarkerOnSelectedOverviewItem(AddMarker marker) throws OperationFailed;
					void AddMarkerAtTime(long timeInPicoseconds, AddMarker marker) throws OperationFailed;
					GetMarkerArray GetMarkers() throws OperationFailed;
					void Export(string outputFilename, string exportName, ExportOptionArray exportOptions) throws OperationFailed;

					StringArray GetAvailableOverviews() throws OperationFailed;
					string GetSelectedOverview() throws OperationFailed;
					void SelectOverview(string overviewName) throws OperationFailed;
					StringArray GetAvailableProtocolLayers() throws OperationFailed;
					string GetSelectedProtocolLayer() throws OperationFailed;
					void SelectProtocolLayer(string protocolLayerName) throws OperationFailed;
					string GetOverviewQuery() throws OperationFailed;
					void SetOverviewQuery(string query) throws OperationFailed;
					int OverviewRootItem() throws OperationFailed;
					string GetOverviewItemDescription(int itemHandle) throws OperationFailed;
					StringArray GetOverviewItemsDescription(HandleArray itemHandles) throws OperationFailed;
					long GetOverviewItemTimeInPicoseconds(int itemHandle) throws OperationFailed;
					TimeArray GetOverviewItemsTimeInPicoseconds(HandleArray itemHandles) throws OperationFailed;
					ByteArray GetOverviewItemData(int itemHandle) throws OperationFailed;
					ByteArrays GetOverviewItemsData(HandleArray itemHandles) throws OperationFailed;
					string GetOverviewItemXmlReport(int itemHandle) throws OperationFailed;
					StringArray GetOverviewItemsXmlReport(HandleArray itemHandles) throws OperationFailed;
					string GetOverviewItemXmlReportFiltered(int itemHandle, StringArray fieldNameFilters) throws OperationFailed;
					StringArray GetOverviewItemsXmlReportFiltered(HandleArray itemHandles, StringArray fieldNameFilters) throws OperationFailed;
					int GetOverviewItemChildCount(int itemHandle) throws OperationFailed;
					int GetOverviewItemChild(int itemHandle, int childIndex) throws OperationFailed;
					HandleArray GetOverviewItemChildren(int itemHandle, int childIndex, int childCount) throws OperationFailed;
					HandleArray SearchOverviewItems(int itemHandle, int childIndex, int childCount, int maxDepth, StringArray descriptionFilters, StringArray fieldNameFilters, StringArray fieldValueFilters) throws OperationFailed;
					void ReleaseAllOverviewItemHandles() throws OperationFailed;
					void SelectOverviewItem(int itemHandle) throws OperationFailed;
					int GetSelectedOverviewItem() throws OperationFailed;

					void GetLogicSignalsState(long timeInPicoseconds, out int logicSignalsState) throws OperationFailed;
					void FindLogicSignalsTransition(long fromTimeInPicoseconds, long toTimeInPicoseconds, int signalsMask, LogicSignalTransitionType transitionType, out int foundLogicSignalsState, out long foundTimeInPicoseconds) throws OperationFailed;

					RunningTaskArray GetRunningTasks() throws OperationFailed;
					void AbortRunningTask(string name) throws OperationFailed;
					ByteArray GetSettings() throws OperationFailed;
					void ConfigureSettings(ByteArray settings) throws OperationFailed;
					void CancelUserInteraction() throws OperationFailed;

					// Deprecated:
					void InsertComment(string comment, string overviewName) throws OperationFailed;
				};
			};
		};
	};
};

#endif 
