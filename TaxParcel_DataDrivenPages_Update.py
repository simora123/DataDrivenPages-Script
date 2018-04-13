# Import system modules
import arcpy, os, sys, time, datetime, traceback, string, numpy

arcpy.env.overwriteOutput = True

# Time stamp variables
currentTime = datetime.datetime.now()
# Date formatted as month-day-year (1-1-2017)
dateToday = currentTime.strftime("%m-%d-%Y")

# Create text file for logging results of script
# Update to directory on SCTF server
file = r'\\YCPCFS\GIS_Projects\IS\Scripts\Python\Logs\ExportPDFUpdate_{}.txt'.format(dateToday)
# Open text file in write mode and log results of script
report = open(file,'w')

# Define functions
# If an error occurred, write line number and error message to log
def ErrorMessageEnvironment(e):
    tb = sys.exc_info()[2]
    report.write("\nFailed at Line %i \n" % tb.tb_lineno)
    report.write('Error: {}\n'.format(str(e)))

# If an error occurred, write line number and error message to log
def ErrorMessageException(e):
    tb = sys.exc_info()[2]
    report.write("\nFailed at Line %i \n" % tb.tb_lineno)
    report.write('Error: {} \n'.format(e.message))

# Write messages to a log file
def message(report,message):
    """ Write a message to a text file
        report is the text file to write the messages to
        report should be defined as report = open(path to file, mode)
         message is the string to write to the file
    """
    timeStamp = time.strftime("%b %d %Y %H:%M:%S")
    report.write("{} {} \n \n".format(timeStamp,message))
    print "{}: ".format(timeStamp) + message
# End functions

# Define Location of Data Driven Layers:
DataDriven_Workplace = r"\\YCPCFS\GIS_Projects\IS\Scripts\Python\Printing\TaxParcel_DataDrivenPages\TaxParcel_DataDrivenPages.gdb"

# Variable used to determine time that script started
ScriptStartTime = datetime.datetime.now()

# Below Variables are used to determine total number of updated parcels per category
# These variables are being populated by the Count Variables in the "districts" For Loop
Total_NewParcel = 0
Total_GeometryChanges = 0
Total_AttributeChanges = 0

# Write message to report
message(report, 'Created empty text file {} \n'.format(file))

try:
    message (report,"""
#------------------------------------------------------------------------------------------------------#
# Name:        TaxParcel_DataDrivenPages_Update.py (Updates Data Driven PDFs on Webserver)             #
#                                                                                                      #
# Purpose:     Script loops thru each taxable districts and looks for Geometry, Attribute,             #
#               or New Parcel compared to the last Tax Parcel update creating a update layer           #
#               called UpdatedParcels_DataDriven under                                                 #
#               O:\IS\Scripts\Python\Printing\TaxParcel_DataDrivenPages\TaxParcel_DataDrivenPages.gdb. #
#               These updated parcel are then used to update the PDF stored on our web server.         #
#               We then run data driven pages                                                          #
#                                                                                                      #
# Authors:     Joseph Simora - York County Planning (YCPC)                                             #
# Credits:     Kevin Eaton (Philadelphia City) and Jacob Trimmer (YCPC)                                #
# Created:     February 01 2018                                                                        #
# Revised:     February 21 2018                                                                        #
# Copyright:   (c) York County Planning Commission                                                     #
#------------------------------------------------------------------------------------------------------#
""")
    # Define Location of Tax Parcel Location:
    arcpy.env.workspace = r'\\YCPCFS\GIS_Projects\IS\Projects\Parcel_Tax_Finder\Parcel_Tax_Finder_JOINBYCOUNTY.gdb\Parcel_Tax_Layers'

    # Variable used output of FList. This defines the most previous tax parcel update vs. the most recent
    datetime_list = ""

    # Lists All Tax Parcel Outputs in Tax Parcel Location:
    FList = arcpy.ListFeatureClasses("Parcel_new_SpatialJoin_*")
    # List used to build all Tax Districts from Search Cursor
    DistrictList = []

    # For Loop: Loops thru FList and populates date_list variable
    for f in FList:
        DateType = f.split("_")[3]
        datetime_list = datetime_list + "," + f.split("_")[3]

    # Variable determines the last updated Tax Parcel Output from FList
    lastupdate = datetime_list.split(",")[-1]
    # Variable determines the previous updated Tax Parcel Output from FList
    previousupdate = datetime_list.split(",")[-2]

    # Variable used to find last updated tax parcel update from Tax Parcel Location
    recent = os.path.join(arcpy.env.workspace, "Parcel_new_SpatialJoin_" + lastupdate)
    # Variable used to find previous updated tax parcel update from Tax Parcel Location
    previous = os.path.join(arcpy.env.workspace, "Parcel_new_SpatialJoin_" + previousupdate)

    # Step used to delete old Tax Parcel Update Information
    message (report, "Deleting Old TaxParcel Update Information\n")
    arcpy.DeleteFeatures_management(os.path.join(DataDriven_Workplace,"UpdatedParcels_DataDriven"))

    # Step is varify that script is using the proper "previous" layer from Tax Parcel Location
    message (report, "Previous Parcel Tax Layer is:\n" + previous +"\n")
    # Step is varify that script is using the proper "recent" layer from Tax Parcel Location
    message (report, "Most Recent Parcel Tax Layer is:\n" + recent + "\n")

    # Step used to overwrite and creat a new "recent" tax parcel layer in Data Driven Location
    message (report, "Creating {}\n".format(os.path.join(DataDriven_Workplace,"RecentTaxParcel")))
    arcpy.Select_analysis(recent, os.path.join(DataDriven_Workplace,"RecentTaxParcel"))

    # Step used to overwrite and creat a new "older" tax parcel layer in Data Driven Location
    message (report, "Creating {}\n".format(os.path.join(DataDriven_Workplace,"OlderTaxParcel")))
    arcpy.Select_analysis(previous, os.path.join(DataDriven_Workplace,"OlderTaxParcel"))

    # Search Cursor Used to populate District List
    with arcpy.da.SearchCursor(os.path.join(DataDriven_Workplace,"Copy_Layer"), ['DIST_NEW']) as cursor:
        for row in cursor:
            DistrictList.append(row)
    del row

    # Deletes Lock on FList
    del f

    # Variable to sort FList. Can't get this to work
    #Dsort = DistrictList.sort

    # For Loop:
    # Loops thru DistrictList which is being populated by Search Cursor
    for districts in DistrictList:
        message (report, "Starting Update and Appending Process for Tax District Number {}\n".format(districts))

        # For Loop Variables
        Attribute_Change = os.path.join(DataDriven_Workplace,"UpdatedParcels_DataDriven_AttributeChange")
        Geometry_Change = os.path.join(DataDriven_Workplace,"UpdatedParcels_DataDriven_GeometryChange")
        New_Parcel = os.path.join(DataDriven_Workplace,"UpdatedParcels_DataDriven_NewParcel")

        # Variables for Count. These will populate Total Counts
        For_Attribute_Count = 0
        For_Geometry_Count = 0
        For_NewParcel_Count = 0

        # Where clause variable used in For Loop
        where = """ "DIST_NEW" = '%s' """ % districts

        # message (report, "Creating Layer Files called {} and {}\n".format("RecentTaxParcel","OlderTaxParcel"))
        # Process: Make Feature Layer
        arcpy.MakeFeatureLayer_management(os.path.join(DataDriven_Workplace,"RecentTaxParcel"), "RecentTaxParcel_Layer", where, "", "OBJECTID OBJECTID VISIBLE NONE;\
        Shape Shape VISIBLE NONE;PIDN_LEASE PIDN_LEASE VISIBLE NONE;\
        Shape_Length Shape_Length VISIBLE NONE;\
        Shape_Area Shape_Area VISIBLE NONE;\
        PIDN_LEASE_1 PIDN_LEASE_1 VISIBLE NONE;\
        PIDN PIDN VISIBLE NONE;\
        DEED_BK DEED_BK VISIBLE NONE;\
        DEED_PG DEED_PG VISIBLE NONE;\
        PROPADR PROPADR VISIBLE NONE;\
        OWNER_FULL OWNER_FULL VISIBLE NONE;\
        OWN_NAME1 OWN_NAME1 VISIBLE NONE;\
        OWN_NAME2 OWN_NAME2 VISIBLE NONE;\
        MAIL_ADDR_FULL MAIL_ADDR_FULL VISIBLE NONE;\
        MAIL_ADDR1 MAIL_ADDR1 VISIBLE NONE;\
        MAIL_ADDR2 MAIL_ADDR2 VISIBLE NONE;\
        MAIL_ADDR3 MAIL_ADDR3 VISIBLE NONE;\
        PREV_OWNER PREV_OWNER VISIBLE NONE;\
        CLASS CLASS VISIBLE NONE;\
        LUC LUC VISIBLE NONE;\
        ACRES ACRES VISIBLE NONE;\
        STYLE STYLE VISIBLE NONE;\
        NUM_STORIE NUM_STORIE VISIBLE NONE;\
        RES_LIVING_AREA RES_LIVING_AREA VISIBLE NONE;\
        YRBLT YRBLT VISIBLE NONE;\
        CLEAN_GREEN CLEAN_GREEN VISIBLE NONE;\
        HEATSYS HEATSYS VISIBLE NONE;\
        FUEL FUEL VISIBLE NONE;\
        UTILITY UTILITY VISIBLE NONE;\
        APRLAND APRLAND VISIBLE NONE;\
        APRBLDG APRBLDG VISIBLE NONE;\
        APRTOTAL APRTOTAL VISIBLE NONE;\
        SALEDT SALEDT VISIBLE NONE;\
        PRICE PRICE VISIBLE NONE;\
        PREV_PRICE PREV_PRICE VISIBLE NONE;\
        SCHOOL_DIS SCHOOL_DIS VISIBLE NONE;\
        COMM_STRUC COMM_STRUC VISIBLE NONE;\
        COMM_YEAR_BUILT COMM_YEAR_BUILT VISIBLE NONE;\
        COMM_BUILDING_SQ_FT COMM_BUILDING_SQ_FT VISIBLE NONE;\
        GRADE GRADE VISIBLE NONE;\
        CDU CDU VISIBLE NONE;\
        DIST_NEW DIST_NEW VISIBLE NONE;\
        MUNICIPAL MUNICIPAL VISIBLE NONE;\
        SCHOOL SCHOOL VISIBLE NONE;\
        COUNTY COUNTY VISIBLE NONE;\
        Muni_Tax_Total Muni_Tax_Total VISIBLE NONE;\
        School_Tax_Total School_Tax_Total VISIBLE NONE;\
        County_Tax_Total County_Tax_Total VISIBLE NONE;\
        Total_Tax Total_Tax VISIBLE NONE;\
        TAX1 TAX1 VISIBLE NONE;\
        TAX2 TAX2 VISIBLE NONE;\
        TAX3 TAX3 VISIBLE NONE;\
        TAX4 TAX4 VISIBLE NONE;\
        TAX5 TAX5 VISIBLE NONE;\
        OTHER_TAX OTHER_TAX VISIBLE NONE;\
        ABTYPE ABTYPE VISIBLE NONE;\
        FACE_TOTAL FACE_TOTAL VISIBLE NONE;\
        ABTYPE_1 ABTYPE_1 VISIBLE NONE;\
        FACE_TOTAL_1 FACE_TOTAL_1 VISIBLE NONE;\
        HOMESTEAD HOMESTEAD VISIBLE NONE;\
        FARMSTEAD FARMSTEAD VISIBLE NONE;\
        PROGRAM PROGRAM VISIBLE NONE;\
        Shape_length Shape_length VISIBLE NONE;\
        Shape_area Shape_area VISIBLE NONE")

        # Process: Make Feature Layer
        arcpy.MakeFeatureLayer_management(os.path.join(DataDriven_Workplace,"OlderTaxParcel"), "OlderTaxParcel_Layer", where, "", "OBJECTID OBJECTID VISIBLE NONE;\
        Shape Shape VISIBLE NONE;\PIDN_LEASE PIDN_LEASE VISIBLE NONE;\
        Shape_Length Shape_Length VISIBLE NONE;\
        Shape_Area Shape_Area VISIBLE NONE;\
        PIDN_LEASE_1 PIDN_LEASE_1 VISIBLE NONE;\
        PIDN PIDN VISIBLE NONE;\
        DEED_BK DEED_BK VISIBLE NONE;\
        DEED_PG DEED_PG VISIBLE NONE;\
        PROPADR PROPADR VISIBLE NONE;\
        OWNER_FULL OWNER_FULL VISIBLE NONE;\
        OWN_NAME1 OWN_NAME1 VISIBLE NONE;\
        OWN_NAME2 OWN_NAME2 VISIBLE NONE;\
        MAIL_ADDR_FULL MAIL_ADDR_FULL VISIBLE NONE;\
        MAIL_ADDR1 MAIL_ADDR1 VISIBLE NONE;\
        MAIL_ADDR2 MAIL_ADDR2 VISIBLE NONE;\
        MAIL_ADDR3 MAIL_ADDR3 VISIBLE NONE;\
        PREV_OWNER PREV_OWNER VISIBLE NONE;\
        CLASS CLASS VISIBLE NONE;\
        LUC LUC VISIBLE NONE;\
        ACRES ACRES VISIBLE NONE;\
        STYLE STYLE VISIBLE NONE;\
        NUM_STORIE NUM_STORIE VISIBLE NONE;\
        RES_LIVING_AREA RES_LIVING_AREA VISIBLE NONE;\
        YRBLT YRBLT VISIBLE NONE;\
        CLEAN_GREEN CLEAN_GREEN VISIBLE NONE;\
        HEATSYS HEATSYS VISIBLE NONE;\
        FUEL FUEL VISIBLE NONE;\
        UTILITY UTILITY VISIBLE NONE;\
        APRLAND APRLAND VISIBLE NONE;\
        APRBLDG APRBLDG VISIBLE NONE;\
        APRTOTAL APRTOTAL VISIBLE NONE;\
        SALEDT SALEDT VISIBLE NONE;\
        PRICE PRICE VISIBLE NONE;\
        PREV_PRICE PREV_PRICE VISIBLE NONE;\
        SCHOOL_DIS SCHOOL_DIS VISIBLE NONE;\
        COMM_STRUC COMM_STRUC VISIBLE NONE;\
        COMM_YEAR_BUILT COMM_YEAR_BUILT VISIBLE NONE;\
        COMM_BUILDING_SQ_FT COMM_BUILDING_SQ_FT VISIBLE NONE;\
        GRADE GRADE VISIBLE NONE;\
        CDU CDU VISIBLE NONE;\
        DIST_NEW DIST_NEW VISIBLE NONE;\
        MUNICIPAL MUNICIPAL VISIBLE NONE;\
        SCHOOL SCHOOL VISIBLE NONE;\
        COUNTY COUNTY VISIBLE NONE;\
        Muni_Tax_Total Muni_Tax_Total VISIBLE NONE;\
        School_Tax_Total School_Tax_Total VISIBLE NONE;\
        County_Tax_Total County_Tax_Total VISIBLE NONE;\
        Total_Tax Total_Tax VISIBLE NONE;\
        TAX1 TAX1 VISIBLE NONE;\
        TAX2 TAX2 VISIBLE NONE;\
        TAX3 TAX3 VISIBLE NONE;\
        TAX4 TAX4 VISIBLE NONE;\
        TAX5 TAX5 VISIBLE NONE;\
        OTHER_TAX OTHER_TAX VISIBLE NONE;\
        ABTYPE ABTYPE VISIBLE NONE;\
        FACE_TOTAL FACE_TOTAL VISIBLE NONE;\
        ABTYPE_1 ABTYPE_1 VISIBLE NONE;\
        FACE_TOTAL_1 FACE_TOTAL_1 VISIBLE NONE;\
        HOMESTEAD HOMESTEAD VISIBLE NONE;\
        FARMSTEAD FARMSTEAD VISIBLE NONE;\
        PROGRAM PROGRAM VISIBLE NONE;\
        Shape_length Shape_length VISIBLE NONE;\
        Shape_area Shape_area VISIBLE NONE")

#####################################################################################  Starting Find New Parcels Section   #######################################################################################################################################


        # This section uses the layer files OlderTaxParcel and RecentTaxParcel to look for New Parcels
        message (report, "Starting Find New Parcels not from last update:\n {}\n".format(os.path.join(DataDriven_Workplace,"OlderTaxParcel")))

        # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
        # The following inputs are layers or table views: "RecentTaxParcel_Layer", "OlderTaxParcel_Layer"
        arcpy.SpatialJoin_analysis("RecentTaxParcel_Layer", "OlderTaxParcel_Layer", os.path.join(DataDriven_Workplace,"UnionNewParcel"), "JOIN_ONE_TO_ONE", "KEEP_ALL",\
         "PIDN_LEASE \"PIDN_LEASE\" true true false 18 Text 0 0 ,First,#,RecentTaxParcel_Layer,PIDN_LEASE,-1,-1;\
         PIDN_LEASE_1 \"PIDN_LEASE\" true true false 18 Text 0 0 ,First,#,RecentTaxParcel_Layer,PIDN_LEASE_1,-1,-1;\
         PIDN \"PIDN\" true true false 13 Text 0 0 ,First,#,RecentTaxParcel_Layer,PIDN,-1,-1;\
         DEED_BK \"DEED_BK\" true true false 8 Text 0 0 ,First,#,RecentTaxParcel_Layer,DEED_BK,-1,-1;\
         DEED_PG \"DEED_PG\" true true false 8 Text 0 0 ,First,#,RecentTaxParcel_Layer,DEED_PG,-1,-1;\
         PROPADR \"PROPADR\" true true false 54 Text 0 0 ,First,#,RecentTaxParcel_Layer,PROPADR,-1,-1;\
         OWNER_FULL \"OWNER_FULL\" true true false 81 Text 0 0 ,First,#,RecentTaxParcel_Layer,OWNER_FULL,-1,-1;\
         OWN_NAME1 \"OWN_NAME1\" true true false 40 Text 0 0 ,First,#,RecentTaxParcel_Layer,OWN_NAME1,-1,-1;\
         OWN_NAME2 \"OWN_NAME2\" true true false 40 Text 0 0 ,First,#,RecentTaxParcel_Layer,OWN_NAME2,-1,-1;\
         MAIL_ADDR_FULL \"MAIL_ADDR_FULL\" true true false 124 Text 0 0 ,First,#,RecentTaxParcel_Layer,MAIL_ADDR_FULL,-1,-1;\
         MAIL_ADDR1 \"MAIL_ADDR1\" true true false 40 Text 0 0 ,First,#,RecentTaxParcel_Layer,MAIL_ADDR1,-1,-1;\
         MAIL_ADDR2 \"MAIL_ADDR2\" true true false 40 Text 0 0 ,First,#,RecentTaxParcel_Layer,MAIL_ADDR2,-1,-1;\
         MAIL_ADDR3 \"MAIL_ADDR3\" true true false 40 Text 0 0 ,First,#,RecentTaxParcel_Layer,MAIL_ADDR3,-1,-1;\
         PREV_OWNER \"PREV_OWNER\" true true false 40 Text 0 0 ,First,#,RecentTaxParcel_Layer,PREV_OWNER,-1,-1;\
         CLASS \"CLASS\" true true false 1 Text 0 0 ,First,#,RecentTaxParcel_Layer,CLASS,-1,-1;\
         LUC \"LUC\" true true false 4 Text 0 0 ,First,#,RecentTaxParcel_Layer,LUC,-1,-1;\
         ACRES \"ACRES\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,ACRES,-1,-1;\
         STYLE \"STYLE\" true true false 2 Text 0 0 ,First,#,RecentTaxParcel_Layer,STYLE,-1,-1;\
         NUM_STORIE \"NUM_STORIE\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,NUM_STORIE,-1,-1;\
         RES_LIVING_AREA \"RES_LIVING_ARE\" true true false 4 Long 0 0 ,First,#,RecentTaxParcel_Layer,RES_LIVING_AREA,-1,-1;\
         YRBLT \"YRBLT\" true true false 2 Short 0 0 ,First,#,RecentTaxParcel_Layer,YRBLT,-1,-1;\
         CLEAN_GREEN \"CLEAN_GREEN\" true true false 3 Text 0 0 ,First,#,RecentTaxParcel_Layer,CLEAN_GREEN,-1,-1;\
         HEATSYS \"HEATSYS\" true true false 2 Short 0 0 ,First,#,RecentTaxParcel_Layer,HEATSYS,-1,-1;\
         FUEL \"FUEL\" true true false 2 Short 0 0 ,First,#,RecentTaxParcel_Layer,FUEL,-1,-1;\
         UTILITY \"UTILITY\" true true false 40 Text 0 0 ,First,#,RecentTaxParcel_Layer,UTILITY,-1,-1;\
         APRLAND \"APRLAND\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,APRLAND,-1,-1;\
         APRBLDG \"APRBLDG\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,APRBLDG,-1,-1;\
         APRTOTAL \"APRTOTAL\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,APRTOTAL,-1,-1;\
         SALEDT \"SALEDT\" true true false 11 Text 0 0 ,First,#,RecentTaxParcel_Layer,SALEDT,-1,-1;\
         PRICE \"PRICE\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,PRICE,-1,-1;\
         PREV_PRICE \"PREV_PRICE\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,PREV_PRICE,-1,-1;\
         SCHOOL_DIS \"SCHOOL_DIS\" true true false 5 Text 0 0 ,First,#,RecentTaxParcel_Layer,SCHOOL_DIS,-1,-1;\
         COMM_STRUC \"COMM_STRUC\" true true false 3 Text 0 0 ,First,#,RecentTaxParcel_Layer,COMM_STRUC,-1,-1;\
         COMM_YEAR_BUILT \"COMM_YEAR_BUILT\" true true false 4 Long 0 0 ,First,#,RecentTaxParcel_Layer,COMM_YEAR_BUILT,-1,-1;\
         COMM_BUILDING_SQ_FT \"COMM_BUILDING_SQ_FT\" true true false 4 Long 0 0 ,First,#,RecentTaxParcel_Layer,COMM_BUILDING_SQ_FT,-1,-1;\
         GRADE \"GRADE\" true true false 2 Text 0 0 ,First,#,RecentTaxParcel_Layer,GRADE,-1,-1;\
         CDU \"CDU\" true true false 2 Text 0 0 ,First,#,RecentTaxParcel_Layer,CDU,-1,-1;\
         DIST_NEW \"DIST_NEW\" true true false 3 Text 0 0 ,First,#,RecentTaxParcel_Layer,DIST_NEW,-1,-1;\
         MUNICIPAL \"MUNICIPAL\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,MUNICIPAL,-1,-1;\
         SCHOOL \"SCHOOL\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,SCHOOL,-1,-1;\
         COUNTY \"COUNTY\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,COUNTY,-1,-1;\
         Muni_Tax_Total \"Muni_Tax_Total\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,Muni_Tax_Total,-1,-1;\
         School_Tax_Total \"School_Tax_Total\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,School_Tax_Total,-1,-1;\
         County_Tax_Total \"County_Tax_Total\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,County_Tax_Total,-1,-1;\
         Total_Tax \"Total_Tax\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,Total_Tax,-1,-1;\
         TAX1 \"TAX1\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,TAX1,-1,-1;\
         TAX2 \"TAX2\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,TAX2,-1,-1;\
         TAX3 \"TAX3\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,TAX3,-1,-1;\
         TAX4 \"TAX4\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,TAX4,-1,-1;\
         TAX5 \"TAX5\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,TAX5,-1,-1;\
         OTHER_TAX \"OTHER_TAX\" true true false 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,OTHER_TAX,-1,-1;\
         ABTYPE \"ABTYPE\" true true false 254 Text 0 0 ,First,#,RecentTaxParcel_Layer,ABTYPE,-1,-1;\
         FACE_TOTAL \"FACE_TOTAL\" true true false 50 Text 0 0 ,First,#,RecentTaxParcel_Layer,FACE_TOTAL,-1,-1;\
         ABTYPE_1 \"ABTYPE_1\" true true false 254 Text 0 0 ,First,#,RecentTaxParcel_Layer,ABTYPE_1,-1,-1;\
         FACE_TOTAL_1 \"FACE_TOTAL_1\" true true false 50 Text 0 0 ,First,#,RecentTaxParcel_Layer,FACE_TOTAL_1,-1,-1;\
         HOMESTEAD \"HOMESTEAD\" true true false 3 Text 0 0 ,First,#,RecentTaxParcel_Layer,HOMESTEAD,-1,-1;\
         FARMSTEAD \"FARMSTEAD\" true true false 3 Text 0 0 ,First,#,RecentTaxParcel_Layer,FARMSTEAD,-1,-1;\
         PROGRAM \"PROGRAM\" true true false 255 Text 0 0 ,First,#,RecentTaxParcel_Layer,PROGRAM,-1,-1;\
         Shape_Length \"Shape_Length\" false true true 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,Shape_Length,-1,-1;\
         Shape_Area \"Shape_Area\" false true true 8 Double 0 0 ,First,#,RecentTaxParcel_Layer,Shape_Area,-1,-1;\
         PIDN_LEASE_12 \"PIDN_LEASE\" true true false 18 Text 0 0 ,First,#,OlderTaxParcel_Layer,PIDN_LEASE,-1,-1;\
         PIDN_LEASE_12_13 \"PIDN_LEASE\" true true false 18 Text 0 0 ,First,#,OlderTaxParcel_Layer,PIDN_LEASE_1,-1,-1;\
         PIDN_1 \"PIDN\" true true false 13 Text 0 0 ,First,#,OlderTaxParcel_Layer,PIDN,-1,-1;\
         DEED_BK_1 \"DEED_BK\" true true false 8 Text 0 0 ,First,#,OlderTaxParcel_Layer,DEED_BK,-1,-1;\
         DEED_PG_1 \"DEED_PG\" true true false 8 Text 0 0 ,First,#,OlderTaxParcel_Layer,DEED_PG,-1,-1;\
         PROPADR_1 \"PROPADR\" true true false 54 Text 0 0 ,First,#,OlderTaxParcel_Layer,PROPADR,-1,-1;\
         OWNER_FULL_1 \"OWNER_FULL\" true true false 81 Text 0 0 ,First,#,OlderTaxParcel_Layer,OWNER_FULL,-1,-1;\
         OWN_NAME1_1 \"OWN_NAME1\" true true false 40 Text 0 0 ,First,#,OlderTaxParcel_Layer,OWN_NAME1,-1,-1;\
         OWN_NAME2_1 \"OWN_NAME2\" true true false 40 Text 0 0 ,First,#,OlderTaxParcel_Layer,OWN_NAME2,-1,-1;\
         MAIL_ADDR_FULL_1 \"MAIL_ADDR_FULL\" true true false 124 Text 0 0 ,First,#,OlderTaxParcel_Layer,MAIL_ADDR_FULL,-1,-1;\
         MAIL_ADDR1_1 \"MAIL_ADDR1\" true true false 40 Text 0 0 ,First,#,OlderTaxParcel_Layer,MAIL_ADDR1,-1,-1;\
         MAIL_ADDR2_1 \"MAIL_ADDR2\" true true false 40 Text 0 0 ,First,#,OlderTaxParcel_Layer,MAIL_ADDR2,-1,-1;\
         MAIL_ADDR3_1 \"MAIL_ADDR3\" true true false 40 Text 0 0 ,First,#,OlderTaxParcel_Layer,MAIL_ADDR3,-1,-1;\
         PREV_OWNER_1 \"PREV_OWNER\" true true false 40 Text 0 0 ,First,#,OlderTaxParcel_Layer,PREV_OWNER,-1,-1;\
         CLASS_1 \"CLASS\" true true false 1 Text 0 0 ,First,#,OlderTaxParcel_Layer,CLASS,-1,-1;\
         LUC_1 \"LUC\" true true false 4 Text 0 0 ,First,#,OlderTaxParcel_Layer,LUC,-1,-1;\
         ACRES_1 \"ACRES\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,ACRES,-1,-1;\
         STYLE_1 \"STYLE\" true true false 2 Text 0 0 ,First,#,OlderTaxParcel_Layer,STYLE,-1,-1;\
         NUM_STORIE_1 \"NUM_STORIE\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,NUM_STORIE,-1,-1;\
         RES_LIVING_AREA_1 \"RES_LIVING_AREA\" true true false 4 Long 0 0 ,First,#,OlderTaxParcel_Layer,RES_LIVING_AREA,-1,-1;\
         YRBLT_1 \"YRBLT\" true true false 2 Short 0 0 ,First,#,OlderTaxParcel_Layer,YRBLT,-1,-1;\
         CLEAN_GREEN_1 \"CLEAN_GREEN\" true true false 3 Text 0 0 ,First,#,OlderTaxParcel_Layer,CLEAN_GREEN,-1,-1;\
         HEATSYS_1 \"HEATSYS\" true true false 2 Short 0 0 ,First,#,OlderTaxParcel_Layer,HEATSYS,-1,-1;\
         FUEL_1 \"FUEL\" true true false 2 Short 0 0 ,First,#,OlderTaxParcel_Layer,FUEL,-1,-1;\
         UTILITY_1 \"UTILITY\" true true false 40 Text 0 0 ,First,#,OlderTaxParcel_Layer,UTILITY,-1,-1;\
         APRLAND_1 \"APRLAND\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,APRLAND,-1,-1;\
         APRBLDG_1 \"APRBLDG\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,APRBLDG,-1,-1;\
         APRTOTAL_1 \"APRTOTAL\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,APRTOTAL,-1,-1;\
         SALEDT_1 \"SALEDT\" true true false 11 Text 0 0 ,First,#,OlderTaxParcel_Layer,SALEDT,-1,-1;\
         PRICE_1 \"PRICE\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,PRICE,-1,-1;\
         PREV_PRICE_1 \"PREV_PRICE\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,PREV_PRICE,-1,-1;\
         SCHOOL_DIS_1 \"SCHOOL_DIS\" true true false 5 Text 0 0 ,First,#,OlderTaxParcel_Layer,SCHOOL_DIS,-1,-1;\
         COMM_STRUC_1 \"COMM_STRUC\" true true false 3 Text 0 0 ,First,#,OlderTaxParcel_Layer,COMM_STRUC,-1,-1;\
         COMM_YEAR_BUILT_1 \"COMM_YEAR_BUILT\" true true false 4 Long 0 0 ,First,#,OlderTaxParcel_Layer,COMM_YEAR_BUILT,-1,-1;\
         COMM_BUILDING_SQ_FT_1 \"COMM_BUILDING_SQ_FT\" true true false 4 Long 0 0 ,First,#,OlderTaxParcel_Layer,COMM_BUILDING_SQ_FT,-1,-1;\
         GRADE_1 \"GRADE\" true true false 2 Text 0 0 ,First,#,OlderTaxParcel_Layer,GRADE,-1,-1;\
         CDU_1 \"CDU\" true true false 2 Text 0 0 ,First,#,OlderTaxParcel_Layer,CDU,-1,-1;\
         DIST_NEW_1 \"DIST_NEW\" true true false 3 Text 0 0 ,First,#,OlderTaxParcel_Layer,DIST_NEW,-1,-1;\
         MUNICIPAL_1 \"MUNICIPAL_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,MUNICIPAL,-1,-1;\
         SCHOOL_1 \"SCHOOL_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,SCHOOL,-1,-1;\
         COUNTY_1 \"COUNTY_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,COUNTY,-1,-1;\
         Muni_Tax_Total_1 \"Muni_Tax_Total_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,Muni_Tax_Total,-1,-1;\
         School_Tax_Total_1 \"School_Tax_Total_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,School_Tax_Total,-1,-1;\
         County_Tax_Total_1 \"County_Tax_Total_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,County_Tax_Total,-1,-1;\
         Total_Tax_1 \"Total_Tax_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,Total_Tax,-1,-1;\
         TAX1_1 \"TAX1_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,TAX1,-1,-1;\
         TAX2_1 \"TAX2_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,TAX2,-1,-1;\
         TAX3_1 \"TAX3_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,TAX3,-1,-1;\
         TAX4_1 \"TAX4_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,TAX4,-1,-1;\
         TAX5_1 \"TAX5_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,TAX5,-1,-1;\
         OTHER_TAX_1 \"OTHER_TAX_1\" true true false 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,OTHER_TAX,-1,-1;\
         ABTYPE_12 \"ABTYPE_12\" true true false 254 Text 0 0 ,First,#,OlderTaxParcel_Layer,ABTYPE,-1,-1;\
         FACE_TOTAL_12 \"FACE_TOTAL_12\" true true false 50 Text 0 0 ,First,#,OlderTaxParcel_Layer,FACE_TOTAL,-1,-1;\
         ABTYPE_12_13 \"ABTYPE_12_13\" true true false 254 Text 0 0 ,First,#,OlderTaxParcel_Layer,ABTYPE_1,-1,-1;\
         FACE_TOTAL_12_13 \"FACE_TOTAL_12_13\" true true false 50 Text 0 0 ,First,#,OlderTaxParcel_Layer,FACE_TOTAL_1,-1,-1;\
         HOMESTEAD_1 \"HOMESTEAD_1\" true true false 3 Text 0 0 ,First,#,OlderTaxParcel_Layer,HOMESTEAD,-1,-1;\
         FARMSTEAD_1 \"FARMSTEAD_1\" true true false 3 Text 0 0 ,First,#,OlderTaxParcel_Layer,FARMSTEAD,-1,-1;\
         PROGRAM_1 \"PROGRAM_1\" true true false 255 Text 0 0 ,First,#,OlderTaxParcel_Layer,PROGRAM,-1,-1;\
         Shape_Length_1 \"Shape_Length_1\" false true true 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,Shape_Length,-1,-1;\
         Shape_Area_1 \"Shape_Area_1\" false true true 8 Double 0 0 ,First,#,OlderTaxParcel_Layer,Shape_Area,-1,-1", "WITHIN", "", "")

        # The following inputs are layers or table views: "UnionNewParcel"
        arcpy.MakeFeatureLayer_management(os.path.join(DataDriven_Workplace,"UnionNewParcel"), "UnionNewParcel_Layer", "", "", "OBJECTID OBJECTID VISIBLE NONE;Shape Shape VISIBLE NONE;Join_Count Join_Count VISIBLE NONE;TARGET_FID TARGET_FID VISIBLE NONE;PIDN_LEASE PIDN_LEASE VISIBLE NONE;PIDN_LEASE_1 PIDN_LEASE_1 VISIBLE NONE;PIDN PIDN VISIBLE NONE;DEED_BK DEED_BK VISIBLE NONE;DEED_PG DEED_PG VISIBLE NONE;PROPADR PROPADR VISIBLE NONE;OWNER_FULL OWNER_FULL VISIBLE NONE;OWN_NAME1 OWN_NAME1 VISIBLE NONE;OWN_NAME2 OWN_NAME2 VISIBLE NONE;MAIL_ADDR_FULL MAIL_ADDR_FULL VISIBLE NONE;MAIL_ADDR1 MAIL_ADDR1 VISIBLE NONE;MAIL_ADDR2 MAIL_ADDR2 VISIBLE NONE;MAIL_ADDR3 MAIL_ADDR3 VISIBLE NONE;PREV_OWNER PREV_OWNER VISIBLE NONE;CLASS CLASS VISIBLE NONE;LUC LUC VISIBLE NONE;ACRES ACRES VISIBLE NONE;STYLE STYLE VISIBLE NONE;NUM_STORIE NUM_STORIE VISIBLE NONE;RES_LIVING_AREA RES_LIVING_AREA VISIBLE NONE;YRBLT YRBLT VISIBLE NONE;CLEAN_GREEN CLEAN_GREEN VISIBLE NONE;HEATSYS HEATSYS VISIBLE NONE;FUEL FUEL VISIBLE NONE;UTILITY UTILITY VISIBLE NONE;APRLAND APRLAND VISIBLE NONE;APRBLDG APRBLDG VISIBLE NONE;APRTOTAL APRTOTAL VISIBLE NONE;SALEDT SALEDT VISIBLE NONE;PRICE PRICE VISIBLE NONE;PREV_PRICE PREV_PRICE VISIBLE NONE;SCHOOL_DIS SCHOOL_DIS VISIBLE NONE;COMM_STRUC COMM_STRUC VISIBLE NONE;COMM_YEAR_BUILT COMM_YEAR_BUILT VISIBLE NONE;COMM_BUILDING_SQ_FT COMM_BUILDING_SQ_FT VISIBLE NONE;GRADE GRADE VISIBLE NONE;CDU CDU VISIBLE NONE;DIST_NEW DIST_NEW VISIBLE NONE;MUNICIPAL MUNICIPAL VISIBLE NONE;SCHOOL SCHOOL VISIBLE NONE;COUNTY COUNTY VISIBLE NONE;Muni_Tax_Total Muni_Tax_Total VISIBLE NONE;School_Tax_Total School_Tax_Total VISIBLE NONE;County_Tax_Total County_Tax_Total VISIBLE NONE;Total_Tax Total_Tax VISIBLE NONE;TAX1 TAX1 VISIBLE NONE;TAX2 TAX2 VISIBLE NONE;TAX3 TAX3 VISIBLE NONE;TAX4 TAX4 VISIBLE NONE;TAX5 TAX5 VISIBLE NONE;OTHER_TAX OTHER_TAX VISIBLE NONE;ABTYPE ABTYPE VISIBLE NONE;FACE_TOTAL FACE_TOTAL VISIBLE NONE;ABTYPE_1 ABTYPE_1 VISIBLE NONE;FACE_TOTAL_1 FACE_TOTAL_1 VISIBLE NONE;HOMESTEAD HOMESTEAD VISIBLE NONE;FARMSTEAD FARMSTEAD VISIBLE NONE;PROGRAM PROGRAM VISIBLE NONE;PIDN_LEASE_12 PIDN_LEASE_12 VISIBLE NONE;PIDN_LEASE_12_13 PIDN_LEASE_12_13 VISIBLE NONE;PIDN_1 PIDN_1 VISIBLE NONE;DEED_BK_1 DEED_BK_1 VISIBLE NONE;DEED_PG_1 DEED_PG_1 VISIBLE NONE;PROPADR_1 PROPADR_1 VISIBLE NONE;OWNER_FULL_1 OWNER_FULL_1 VISIBLE NONE;OWN_NAME1_1 OWN_NAME1_1 VISIBLE NONE;OWN_NAME2_1 OWN_NAME2_1 VISIBLE NONE;MAIL_ADDR_FULL_1 MAIL_ADDR_FULL_1 VISIBLE NONE;MAIL_ADDR1_1 MAIL_ADDR1_1 VISIBLE NONE;MAIL_ADDR2_1 MAIL_ADDR2_1 VISIBLE NONE;MAIL_ADDR3_1 MAIL_ADDR3_1 VISIBLE NONE;PREV_OWNER_1 PREV_OWNER_1 VISIBLE NONE;CLASS_1 CLASS_1 VISIBLE NONE;LUC_1 LUC_1 VISIBLE NONE;ACRES_1 ACRES_1 VISIBLE NONE;STYLE_1 STYLE_1 VISIBLE NONE;NUM_STORIE_1 NUM_STORIE_1 VISIBLE NONE;RES_LIVING_AREA_1 RES_LIVING_AREA_1 VISIBLE NONE;YRBLT_1 YRBLT_1 VISIBLE NONE;CLEAN_GREEN_1 CLEAN_GREEN_1 VISIBLE NONE;HEATSYS_1 HEATSYS_1 VISIBLE NONE;FUEL_1 FUEL_1 VISIBLE NONE;UTILITY_1 UTILITY_1 VISIBLE NONE;APRLAND_1 APRLAND_1 VISIBLE NONE;APRBLDG_1 APRBLDG_1 VISIBLE NONE;APRTOTAL_1 APRTOTAL_1 VISIBLE NONE;SALEDT_1 SALEDT_1 VISIBLE NONE;PRICE_1 PRICE_1 VISIBLE NONE;PREV_PRICE_1 PREV_PRICE_1 VISIBLE NONE;SCHOOL_DIS_1 SCHOOL_DIS_1 VISIBLE NONE;COMM_STRUC_1 COMM_STRUC_1 VISIBLE NONE;COMM_YEAR_BUILT_1 COMM_YEAR_BUILT_1 VISIBLE NONE;COMM_BUILDING_SQ_FT_1 COMM_BUILDING_SQ_FT_1 VISIBLE NONE;GRADE_1 GRADE_1 VISIBLE NONE;CDU_1 CDU_1 VISIBLE NONE;DIST_NEW_1 DIST_NEW_1 VISIBLE NONE;MUNICIPAL_1 MUNICIPAL_1 VISIBLE NONE;SCHOOL_1 SCHOOL_1 VISIBLE NONE;COUNTY_1 COUNTY_1 VISIBLE NONE;Muni_Tax_Total_1 Muni_Tax_Total_1 VISIBLE NONE;School_Tax_Total_1 School_Tax_Total_1 VISIBLE NONE;County_Tax_Total_1 County_Tax_Total_1 VISIBLE NONE;Total_Tax_1 Total_Tax_1 VISIBLE NONE;TAX1_1 TAX1_1 VISIBLE NONE;TAX2_1 TAX2_1 VISIBLE NONE;TAX3_1 TAX3_1 VISIBLE NONE;TAX4_1 TAX4_1 VISIBLE NONE;TAX5_1 TAX5_1 VISIBLE NONE;OTHER_TAX_1 OTHER_TAX_1 VISIBLE NONE;ABTYPE_12 ABTYPE_12 VISIBLE NONE;FACE_TOTAL_12 FACE_TOTAL_12 VISIBLE NONE;ABTYPE_12_13 ABTYPE_12_13 VISIBLE NONE;FACE_TOTAL_12_13 FACE_TOTAL_12_13 VISIBLE NONE;HOMESTEAD_1 HOMESTEAD_1 VISIBLE NONE;FARMSTEAD_1 FARMSTEAD_1 VISIBLE NONE;PROGRAM_1 PROGRAM_1 VISIBLE NONE;Shape_Length_1 Shape_Length_1 VISIBLE NONE;Shape_Area_1 Shape_Area_1 VISIBLE NONE;Shape_Length Shape_Length VISIBLE NONE;Shape_Area Shape_Area VISIBLE NONE")

        # Process: Select Layer By Attribute
        # Step Selects Features from UnionNewParcel that PIDN_LEASE fields do not match and Join_Count = 1( 1 represents features that are in "recent" layer but not in "older" layer)
        arcpy.SelectLayerByAttribute_management("UnionNewParcel_Layer", "NEW_SELECTION", "PIDN_LEASE <> PIDN_LEASE_12 AND Join_Count = 1")

        # message (report, "Creating {}\n".format(New_Parcel))
        # Step Selects Features from UnionNewParcel and overwrites/copies results to New_Parcel variable
        arcpy.Select_analysis("UnionNewParcel_Layer", New_Parcel, "")

        #message (report, "Adding Field and Calculating {}\n".format(New_Parcel))

        # Process: Add Field
        # Adds field called Type
        arcpy.AddField_management(New_Parcel, "Type", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

        # Process: Calculate Field
        arcpy.CalculateField_management(New_Parcel, "Type", "\"New Parcel\"", "PYTHON", "")

        # Steps used to Tabulate count of new parcels in particular tax district
        message (report, "Calculating New Parcel Count for {}\n".format(New_Parcel))
        NewParcelresult = New_Parcel
        result = arcpy.GetCount_management(NewParcelresult)
        count = int(result.getOutput(0))
        message (report,("Found (" + str(count) + ") New Parcels for Tax District {}\n".format(districts)))
        # Tabulates/Adds count information to New Parcel ForLoop Count
        For_NewParcel_Count = For_NewParcel_Count + count
        # Tabulates/Adds count information to Total New Parcel Count
        Total_NewParcel = Total_NewParcel + count

######################################################################################   Join Step      ######################################################################################################################################################

        # Step used to Join OlderTaxParcel_Layer and Recent_Layer together. This join will be used to determine geometry and attribute changes between Older and Recent Tax Parcel Info per Tax District
        #message (report, "Preparing {} and {} for Join\n".format(os.path.join(DataDriven_Workplace,"RecentTaxParcel"),os.path.join(DataDriven_Workplace,"OlderTaxParcel")))
        arcpy.AddJoin_management("RecentTaxParcel_Layer", "PIDN_LEASE", "OlderTaxParcel_Layer", "PIDN_LEASE", "KEEP_ALL")

######################################################################   Steps Used to Find Differences in Geometry  ######################################################################################################################################################

        # This section uses the layer files OlderTaxParcel and RecentTaxParcel Find Differences in Geometry
        message (report, "Starting Find Parcels with Different Geometry Steps\n")

        # Step used to create a Feature Layer from Older and Recent Feature Layer
        # The following inputs are layers or table views: "RecentTaxParcel_Layer"
        arcpy.MakeFeatureLayer_management("RecentTaxParcel_Layer", "RecentTaxParcel_Geometry", "", "", "RecentTaxParcel.OBJECTID RecentTaxParcel.OBJECTID VISIBLE NONE;\
        RecentTaxParcel.Shape RecentTaxParcel.Shape VISIBLE NONE;RecentTaxParcel.PIDN_LEASE RecentTaxParcel.PIDN_LEASE VISIBLE NONE;RecentTaxParcel.PIDN_LEASE_1 RecentTaxParcel.PIDN_LEASE_1 VISIBLE NONE;\
        RecentTaxParcel.PIDN RecentTaxParcel.PIDN VISIBLE NONE;\
        RecentTaxParcel.DEED_BK RecentTaxParcel.DEED_BK VISIBLE NONE;\
        RecentTaxParcel.DEED_PG RecentTaxParcel.DEED_PG VISIBLE NONE;\
        RecentTaxParcel.PROPADR RecentTaxParcel.PROPADR VISIBLE NONE;\
        RecentTaxParcel.OWNER_FULL RecentTaxParcel.OWNER_FULL VISIBLE NONE;\
        RecentTaxParcel.OWN_NAME1 RecentTaxParcel.OWN_NAME1 VISIBLE NONE;\
        RecentTaxParcel.OWN_NAME2 RecentTaxParcel.OWN_NAME2 VISIBLE NONE;\
        RecentTaxParcel.MAIL_ADDR_FULL RecentTaxParcel.MAIL_ADDR_FULL VISIBLE NONE;\
        RecentTaxParcel.MAIL_ADDR1 RecentTaxParcel.MAIL_ADDR1 VISIBLE NONE;\
        RecentTaxParcel.MAIL_ADDR2 RecentTaxParcel.MAIL_ADDR2 VISIBLE NONE;\
        RecentTaxParcel.MAIL_ADDR3 RecentTaxParcel.MAIL_ADDR3 VISIBLE NONE;\
        RecentTaxParcel.PREV_OWNER RecentTaxParcel.PREV_OWNER VISIBLE NONE;\
        RecentTaxParcel.CLASS RecentTaxParcel.CLASS VISIBLE NONE;\
        RecentTaxParcel.LUC RecentTaxParcel.LUC VISIBLE NONE;\
        RecentTaxParcel.ACRES RecentTaxParcel.ACRES VISIBLE NONE;\
        RecentTaxParcel.STYLE RecentTaxParcel.STYLE VISIBLE NONE;\
        RecentTaxParcel.NUM_STORIE RecentTaxParcel.NUM_STORIE VISIBLE NONE;\
        RecentTaxParcel.RES_LIVING_AREA RecentTaxParcel.RES_LIVING_AREA VISIBLE NONE;\
        RecentTaxParcel.YRBLT RecentTaxParcel.YRBLT VISIBLE NONE;\
        RecentTaxParcel.CLEAN_GREEN RecentTaxParcel.CLEAN_GREEN VISIBLE NONE;\
        RecentTaxParcel.HEATSYS RecentTaxParcel.HEATSYS VISIBLE NONE;\
        RecentTaxParcel.FUEL RecentTaxParcel.FUEL VISIBLE NONE;\
        RecentTaxParcel.UTILITY RecentTaxParcel.UTILITY VISIBLE NONE;\
        RecentTaxParcel.APRLAND RecentTaxParcel.APRLAND VISIBLE NONE;\
        RecentTaxParcel.APRBLDG RecentTaxParcel.APRBLDG VISIBLE NONE;\
        RecentTaxParcel.APRTOTAL RecentTaxParcel.APRTOTAL VISIBLE NONE;\
        RecentTaxParcel.SALEDT RecentTaxParcel.SALEDT VISIBLE NONE;\
        RecentTaxParcel.PRICE RecentTaxParcel.PRICE VISIBLE NONE;\
        RecentTaxParcel.PREV_PRICE RecentTaxParcel.PREV_PRICE VISIBLE NONE;\
        RecentTaxParcel.SCHOOL_DIS RecentTaxParcel.SCHOOL_DIS VISIBLE NONE;\
        RecentTaxParcel.COMM_STRUC RecentTaxParcel.COMM_STRUC VISIBLE NONE;\
        RecentTaxParcel.COMM_YEAR_BUILT RecentTaxParcel.COMM_YEAR_BUILT VISIBLE NONE;\
        RecentTaxParcel.COMM_BUILDING_SQ_FT RecentTaxParcel.COMM_BUILDING_SQ_FT VISIBLE NONE;\
        RecentTaxParcel.GRADE RecentTaxParcel.GRADE VISIBLE NONE;\
        RecentTaxParcel.CDU RecentTaxParcel.CDU VISIBLE NONE;\
        RecentTaxParcel.DIST_NEW RecentTaxParcel.DIST_NEW VISIBLE NONE;\
        RecentTaxParcel.MUNICIPAL RecentTaxParcel.MUNICIPAL VISIBLE NONE;\
        RecentTaxParcel.SCHOOL RecentTaxParcel.SCHOOL VISIBLE NONE;\
        RecentTaxParcel.COUNTY RecentTaxParcel.COUNTY VISIBLE NONE;\
        RecentTaxParcel.Muni_Tax_Total RecentTaxParcel.Muni_Tax_Total VISIBLE NONE;\
        RecentTaxParcel.School_Tax_Total RecentTaxParcel.School_Tax_Total VISIBLE NONE;\
        RecentTaxParcel.County_Tax_Total RecentTaxParcel.County_Tax_Total VISIBLE NONE;\
        RecentTaxParcel.Total_Tax RecentTaxParcel.Total_Tax VISIBLE NONE;\
        RecentTaxParcel.TAX1 RecentTaxParcel.TAX1 VISIBLE NONE;\
        RecentTaxParcel.TAX2 RecentTaxParcel.TAX2 VISIBLE NONE;\
        RecentTaxParcel.TAX3 RecentTaxParcel.TAX3 VISIBLE NONE;\
        RecentTaxParcel.TAX4 RecentTaxParcel.TAX4 VISIBLE NONE;\
        RecentTaxParcel.TAX5 RecentTaxParcel.TAX5 VISIBLE NONE;\
        RecentTaxParcel.OTHER_TAX RecentTaxParcel.OTHER_TAX VISIBLE NONE;\
        RecentTaxParcel.ABTYPE RecentTaxParcel.ABTYPE VISIBLE NONE;\
        RecentTaxParcel.FACE_TOTAL RecentTaxParcel.FACE_TOTAL VISIBLE NONE;\
        RecentTaxParcel.ABTYPE_1 RecentTaxParcel.ABTYPE_1 VISIBLE NONE;\
        RecentTaxParcel.FACE_TOTAL_1 RecentTaxParcel.FACE_TOTAL_1 VISIBLE NONE;\
        RecentTaxParcel.HOMESTEAD RecentTaxParcel.HOMESTEAD VISIBLE NONE;\
        RecentTaxParcel.FARMSTEAD RecentTaxParcel.FARMSTEAD VISIBLE NONE;\
        RecentTaxParcel.PROGRAM RecentTaxParcel.PROGRAM VISIBLE NONE;\
        RecentTaxParcel.Shape_Length RecentTaxParcel.Shape_Length VISIBLE NONE;\
        RecentTaxParcel.Shape_Area RecentTaxParcel.Shape_Area VISIBLE NONE;\
        OlderTaxParcel.OBJECTID OlderTaxParcel.OBJECTID VISIBLE NONE;\
        OlderTaxParcel.PIDN_LEASE OlderTaxParcel.PIDN_LEASE VISIBLE NONE;\
        OlderTaxParcel.PIDN_LEASE_1 OlderTaxParcel.PIDN_LEASE_1 VISIBLE NONE;\
        OlderTaxParcel.PIDN OlderTaxParcel.PIDN VISIBLE NONE;\
        OlderTaxParcel.DEED_BK OlderTaxParcel.DEED_BK VISIBLE NONE\
        ;OlderTaxParcel.DEED_PG OlderTaxParcel.DEED_PG VISIBLE NONE;\
        OlderTaxParcel.PROPADR OlderTaxParcel.PROPADR VISIBLE NONE;\
        OlderTaxParcel.OWNER_FULL OlderTaxParcel.OWNER_FULL VISIBLE NONE;\
        OlderTaxParcel.OWN_NAME1 OlderTaxParcel.OWN_NAME1 VISIBLE NONE;\
        OlderTaxParcel.OWN_NAME2 OlderTaxParcel.OWN_NAME2 VISIBLE NONE;\
        OlderTaxParcel.MAIL_ADDR_FULL OlderTaxParcel.MAIL_ADDR_FULL VISIBLE NONE;\
        OlderTaxParcel.MAIL_ADDR1 OlderTaxParcel.MAIL_ADDR1 VISIBLE NONE;\
        OlderTaxParcel.MAIL_ADDR2 OlderTaxParcel.MAIL_ADDR2 VISIBLE NONE;\
        OlderTaxParcel.MAIL_ADDR3 OlderTaxParcel.MAIL_ADDR3 VISIBLE NONE;\
        OlderTaxParcel.PREV_OWNER OlderTaxParcel.PREV_OWNER VISIBLE NONE;\
        OlderTaxParcel.CLASS OlderTaxParcel.CLASS VISIBLE NONE;\
        OlderTaxParcel.LUC OlderTaxParcel.LUC VISIBLE NONE;\
        OlderTaxParcel.ACRES OlderTaxParcel.ACRES VISIBLE NONE;\
        OlderTaxParcel.STYLE OlderTaxParcel.STYLE VISIBLE NONE;\
        OlderTaxParcel.NUM_STORIE OlderTaxParcel.NUM_STORIE VISIBLE NONE;\
        OlderTaxParcel.RES_LIVING_AREA OlderTaxParcel.RES_LIVING_AREA VISIBLE NONE;\
        OlderTaxParcel.YRBLT OlderTaxParcel.YRBLT VISIBLE NONE;\
        OlderTaxParcel.CLEAN_GREEN OlderTaxParcel.CLEAN_GREEN VISIBLE NONE;\
        OlderTaxParcel.HEATSYS OlderTaxParcel.HEATSYS VISIBLE NONE;\
        OlderTaxParcel.FUEL OlderTaxParcel.FUEL VISIBLE NONE;\
        OlderTaxParcel.UTILITY OlderTaxParcel.UTILITY VISIBLE NONE;\
        OlderTaxParcel.APRLAND OlderTaxParcel.APRLAND VISIBLE NONE;\
        OlderTaxParcel.APRBLDG OlderTaxParcel.APRBLDG VISIBLE NONE;\
        OlderTaxParcel.APRTOTAL OlderTaxParcel.APRTOTAL VISIBLE NONE;\
        OlderTaxParcel.SALEDT OlderTaxParcel.SALEDT VISIBLE NONE;\
        OlderTaxParcel.PRICE OlderTaxParcel.PRICE VISIBLE NONE;\
        OlderTaxParcel.PREV_PRICE OlderTaxParcel.PREV_PRICE VISIBLE NONE;\
        OlderTaxParcel.SCHOOL_DIS OlderTaxParcel.SCHOOL_DIS VISIBLE NONE;\
        OlderTaxParcel.COMM_STRUC OlderTaxParcel.COMM_STRUC VISIBLE NONE;\
        OlderTaxParcel.COMM_YEAR_BUILT OlderTaxParcel.COMM_YEAR_BUILT VISIBLE NONE;\
        OlderTaxParcel.COMM_BUILDING_SQ_FT OlderTaxParcel.COMM_BUILDING_SQ_FT VISIBLE NONE;\
        OlderTaxParcel.GRADE OlderTaxParcel.GRADE VISIBLE NONE;\
        OlderTaxParcel.CDU OlderTaxParcel.CDU VISIBLE NONE;\
        OlderTaxParcel.DIST_NEW OlderTaxParcel.DIST_NEW VISIBLE NONE;\
        OlderTaxParcel.MUNICIPAL OlderTaxParcel.MUNICIPAL VISIBLE NONE;\
        OlderTaxParcel.SCHOOL OlderTaxParcel.SCHOOL VISIBLE NONE;\
        OlderTaxParcel.COUNTY OlderTaxParcel.COUNTY VISIBLE NONE;\
        OlderTaxParcel.Muni_Tax_Total OlderTaxParcel.Muni_Tax_Total VISIBLE NONE;\
        OlderTaxParcel.School_Tax_Total OlderTaxParcel.School_Tax_Total VISIBLE NONE;\
        OlderTaxParcel.County_Tax_Total OlderTaxParcel.County_Tax_Total VISIBLE NONE;\
        OlderTaxParcel.Total_Tax OlderTaxParcel.Total_Tax VISIBLE NONE;\
        OlderTaxParcel.TAX1 OlderTaxParcel.TAX1 VISIBLE NONE;\
        OlderTaxParcel.TAX2 OlderTaxParcel.TAX2 VISIBLE NONE;\
        OlderTaxParcel.TAX3 OlderTaxParcel.TAX3 VISIBLE NONE;\
        OlderTaxParcel.TAX4 OlderTaxParcel.TAX4 VISIBLE NONE;\
        OlderTaxParcel.TAX5 OlderTaxParcel.TAX5 VISIBLE NONE;\
        OlderTaxParcel.OTHER_TAX OlderTaxParcel.OTHER_TAX VISIBLE NONE;\
        OlderTaxParcel.ABTYPE OlderTaxParcel.ABTYPE VISIBLE NONE;\
        OlderTaxParcel.FACE_TOTAL OlderTaxParcel.FACE_TOTAL VISIBLE NONE;\
        OlderTaxParcel.ABTYPE_1 OlderTaxParcel.ABTYPE_1 VISIBLE NONE;\
        OlderTaxParcel.FACE_TOTAL_1 OlderTaxParcel.FACE_TOTAL_1 VISIBLE NONE;\
        OlderTaxParcel.HOMESTEAD OlderTaxParcel.HOMESTEAD VISIBLE NONE;\
        OlderTaxParcel.FARMSTEAD OlderTaxParcel.FARMSTEAD VISIBLE NONE;\
        OlderTaxParcel.PROGRAM OlderTaxParcel.PROGRAM VISIBLE NONE;\
        OlderTaxParcel.Shape_Length OlderTaxParcel.Shape_Length VISIBLE NONE;\
        OlderTaxParcel.Shape_Area OlderTaxParcel.Shape_Area VISIBLE NONE")

        #message (report, "Selecting Parcel that Geometry are different from {} and {}\n".format(os.path.join(DataDriven_Workplace,"RecentTaxParcel"),os.path.join(DataDriven_Workplace,"OlderTaxParcel")))
        # Step Selects Features from RecentTaxParcel_Geometry Feature Layer that Shape_Area fields do not match
        arcpy.SelectLayerByAttribute_management("RecentTaxParcel_Geometry", "NEW_SELECTION", "RecentTaxParcel.Shape_Area <> OlderTaxParcel.Shape_Area")

        #message (report, "Creating {}\n".format(Geometry_Change))
        # Step Selects Features from RecentTaxParcel_Geometry and overwrites/copies results to Geometry_Change variable
        arcpy.Select_analysis("RecentTaxParcel_Geometry", Geometry_Change, "")

        #message (report, "Adding Field and Calculating {}\n".format(Geometry_Change))
        # Creates Field Type
        arcpy.AddField_management(Geometry_Change, "Type", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

        # Calculates Field Type
        arcpy.CalculateField_management(Geometry_Change, "Type", "\"Geometry Change\"", "PYTHON", "")

        # Steps used to Tabulate count of Geometry Changes in particular tax district
        message (report, "Calculating Geometry Count for {}\n".format(Geometry_Change))
        Geometryresult = Geometry_Change
        result = arcpy.GetCount_management(Geometryresult)
        count = int(result.getOutput(0))
        message (report,("Found (" + str(count) + ") Geometry Changes for Tax District {}\n".format(districts)))
        # Tabulates/Adds count information to Geometry Change ForLoop Count
        For_Geometry_Count = For_Geometry_Count + count
        # Tabulates/Adds count information to Geometry Change Total Count
        Total_GeometryChanges = Total_GeometryChanges + count

####################################################################   Find Parcels with Different Attribute Steps      ################################################################################################################################################################

        # This section uses the layer files OlderTaxParcel and RecentTaxParcel Find Differences in Attributes
        message (report, "Starting Find Parcels with Different Attribute Steps\n")

        # Process: Make Feature Layer called RecentTaxParcel_Attributes from RecentTaxParcel_Layer
        arcpy.MakeFeatureLayer_management("RecentTaxParcel_Layer", "RecentTaxParcel_Attributes", "", "", "RecentTaxParcel.OBJECTID RecentTaxParcel.OBJECTID VISIBLE NONE;\
        RecentTaxParcel.Shape RecentTaxParcel.Shape VISIBLE NONE;\
        RecentTaxParcel.PIDN_LEASE RecentTaxParcel.PIDN_LEASE VISIBLE NONE;\
        RecentTaxParcel.PIDN_LEASE_1 RecentTaxParcel.PIDN_LEASE_1 VISIBLE NONE;\
        RecentTaxParcel.PIDN RecentTaxParcel.PIDN VISIBLE NONE;\
        RecentTaxParcel.DEED_BK RecentTaxParcel.DEED_BK VISIBLE NONE;\
        RecentTaxParcel.DEED_PG RecentTaxParcel.DEED_PG VISIBLE NONE;\
        RecentTaxParcel.PROPADR RecentTaxParcel.PROPADR VISIBLE NONE;\
        RecentTaxParcel.OWNER_FULL RecentTaxParcel.OWNER_FULL VISIBLE NONE;\
        RecentTaxParcel.OWN_NAME1 RecentTaxParcel.OWN_NAME1 VISIBLE NONE;\
        RecentTaxParcel.OWN_NAME2 RecentTaxParcel.OWN_NAME2 VISIBLE NONE;\
        RecentTaxParcel.MAIL_ADDR_FULL RecentTaxParcel.MAIL_ADDR_FULL VISIBLE NONE;\
        RecentTaxParcel.MAIL_ADDR1 RecentTaxParcel.MAIL_ADDR1 VISIBLE NONE;\
        RecentTaxParcel.MAIL_ADDR2 RecentTaxParcel.MAIL_ADDR2 VISIBLE NONE;\
        RecentTaxParcel.MAIL_ADDR3 RecentTaxParcel.MAIL_ADDR3 VISIBLE NONE;\
        RecentTaxParcel.PREV_OWNER RecentTaxParcel.PREV_OWNER VISIBLE NONE;\
        RecentTaxParcel.CLASS RecentTaxParcel.CLASS VISIBLE NONE;\
        RecentTaxParcel.LUC RecentTaxParcel.LUC VISIBLE NONE;\
        RecentTaxParcel.ACRES RecentTaxParcel.ACRES VISIBLE NONE;\
        RecentTaxParcel.STYLE RecentTaxParcel.STYLE VISIBLE NONE;\
        RecentTaxParcel.NUM_STORIE RecentTaxParcel.NUM_STORIE VISIBLE NONE;\
        RecentTaxParcel.RES_LIVING_AREA RecentTaxParcel.RES_LIVING_AREA VISIBLE NONE;\
        RecentTaxParcel.YRBLT RecentTaxParcel.YRBLT VISIBLE NONE;\
        RecentTaxParcel.CLEAN_GREEN RecentTaxParcel.CLEAN_GREEN VISIBLE NONE;\
        RecentTaxParcel.HEATSYS RecentTaxParcel.HEATSYS VISIBLE NONE;\
        RecentTaxParcel.FUEL RecentTaxParcel.FUEL VISIBLE NONE;\
        RecentTaxParcel.UTILITY RecentTaxParcel.UTILITY VISIBLE NONE;\
        RecentTaxParcel.APRLAND RecentTaxParcel.APRLAND VISIBLE NONE;\
        RecentTaxParcel.APRBLDG RecentTaxParcel.APRBLDG VISIBLE NONE;\
        RecentTaxParcel.APRTOTAL RecentTaxParcel.APRTOTAL VISIBLE NONE;\
        RecentTaxParcel.SALEDT RecentTaxParcel.SALEDT VISIBLE NONE;\
        RecentTaxParcel.PRICE RecentTaxParcel.PRICE VISIBLE NONE;\
        RecentTaxParcel.PREV_PRICE RecentTaxParcel.PREV_PRICE VISIBLE NONE;\
        RecentTaxParcel.SCHOOL_DIS RecentTaxParcel.SCHOOL_DIS VISIBLE NONE;\
        RecentTaxParcel.COMM_STRUC RecentTaxParcel.COMM_STRUC VISIBLE NONE;\
        RecentTaxParcel.COMM_YEAR_BUILT RecentTaxParcel.COMM_YEAR_BUILT VISIBLE NONE;\
        RecentTaxParcel.COMM_BUILDING_SQ_FT RecentTaxParcel.COMM_BUILDING_SQ_FT VISIBLE NONE;\
        RecentTaxParcel.GRADE RecentTaxParcel.GRADE VISIBLE NONE;\
        RecentTaxParcel.CDU RecentTaxParcel.CDU VISIBLE NONE;\
        RecentTaxParcel.DIST_NEW RecentTaxParcel.DIST_NEW VISIBLE NONE;\
        RecentTaxParcel.MUNICIPAL RecentTaxParcel.MUNICIPAL VISIBLE NONE;\
        RecentTaxParcel.SCHOOL RecentTaxParcel.SCHOOL VISIBLE NONE;\
        RecentTaxParcel.COUNTY RecentTaxParcel.COUNTY VISIBLE NONE;\
        RecentTaxParcel.Muni_Tax_Total RecentTaxParcel.Muni_Tax_Total VISIBLE NONE;\
        RecentTaxParcel.School_Tax_Total RecentTaxParcel.School_Tax_Total VISIBLE NONE;\
        RecentTaxParcel.County_Tax_Total RecentTaxParcel.County_Tax_Total VISIBLE NONE;\
        RecentTaxParcel.Total_Tax RecentTaxParcel.Total_Tax VISIBLE NONE;\
        RecentTaxParcel.TAX1 RecentTaxParcel.TAX1 VISIBLE NONE;\
        RecentTaxParcel.TAX2 RecentTaxParcel.TAX2 VISIBLE NONE;\
        RecentTaxParcel.TAX3 RecentTaxParcel.TAX3 VISIBLE NONE;\
        RecentTaxParcel.TAX4 RecentTaxParcel.TAX4 VISIBLE NONE;\
        RecentTaxParcel.TAX5 RecentTaxParcel.TAX5 VISIBLE NONE;\
        RecentTaxParcel.OTHER_TAX RecentTaxParcel.OTHER_TAX VISIBLE NONE;\
        RecentTaxParcel.ABTYPE RecentTaxParcel.ABTYPE VISIBLE NONE;\
        RecentTaxParcel.FACE_TOTAL RecentTaxParcel.FACE_TOTAL VISIBLE NONE;\
        RecentTaxParcel.ABTYPE_1 RecentTaxParcel.ABTYPE_1 VISIBLE NONE;\
        RecentTaxParcel.FACE_TOTAL_1 RecentTaxParcel.FACE_TOTAL_1 VISIBLE NONE;\
        RecentTaxParcel.HOMESTEAD RecentTaxParcel.HOMESTEAD VISIBLE NONE;\
        RecentTaxParcel.FARMSTEAD RecentTaxParcel.FARMSTEAD VISIBLE NONE;\
        RecentTaxParcel.PROGRAM RecentTaxParcel.PROGRAM VISIBLE NONE;\
        RecentTaxParcel.Shape_Length RecentTaxParcel.Shape_Length VISIBLE NONE;\
        RecentTaxParcel.Shape_Area RecentTaxParcel.Shape_Area VISIBLE NONE;\
        OlderTaxParcel.OBJECTID OlderTaxParcel.OBJECTID VISIBLE NONE;\
        OlderTaxParcel.PIDN_LEASE OlderTaxParcel.PIDN_LEASE VISIBLE NONE;\
        OlderTaxParcel.PIDN_LEASE_1 OlderTaxParcel.PIDN_LEASE_1 VISIBLE NONE;\
        OlderTaxParcel.PIDN OlderTaxParcel.PIDN VISIBLE NONE;\
        OlderTaxParcel.DEED_BK OlderTaxParcel.DEED_BK VISIBLE NONE;\
        OlderTaxParcel.DEED_PG OlderTaxParcel.DEED_PG VISIBLE NONE;\
        OlderTaxParcel.PROPADR OlderTaxParcel.PROPADR VISIBLE NONE;\
        OlderTaxParcel.OWNER_FULL OlderTaxParcel.OWNER_FULL VISIBLE NONE;\
        OlderTaxParcel.OWN_NAME1 OlderTaxParcel.OWN_NAME1 VISIBLE NONE;\
        OlderTaxParcel.OWN_NAME2 OlderTaxParcel.OWN_NAME2 VISIBLE NONE;\
        OlderTaxParcel.MAIL_ADDR_FULL OlderTaxParcel.MAIL_ADDR_FULL VISIBLE NONE;\
        OlderTaxParcel.MAIL_ADDR1 OlderTaxParcel.MAIL_ADDR1 VISIBLE NONE;\
        OlderTaxParcel.MAIL_ADDR2 OlderTaxParcel.MAIL_ADDR2 VISIBLE NONE;\
        OlderTaxParcel.MAIL_ADDR3 OlderTaxParcel.MAIL_ADDR3 VISIBLE NONE;\
        OlderTaxParcel.PREV_OWNER OlderTaxParcel.PREV_OWNER VISIBLE NONE;\
        OlderTaxParcel.CLASS OlderTaxParcel.CLASS VISIBLE NONE;\
        OlderTaxParcel.LUC OlderTaxParcel.LUC VISIBLE NONE;\
        OlderTaxParcel.ACRES OlderTaxParcel.ACRES VISIBLE NONE;\
        OlderTaxParcel.STYLE OlderTaxParcel.STYLE VISIBLE NONE;\
        OlderTaxParcel.NUM_STORIE OlderTaxParcel.NUM_STORIE VISIBLE NONE;\
        OlderTaxParcel.RES_LIVING_AREA OlderTaxParcel.RES_LIVING_AREA VISIBLE NONE;\
        OlderTaxParcel.YRBLT OlderTaxParcel.YRBLT VISIBLE NONE;\
        OlderTaxParcel.CLEAN_GREEN OlderTaxParcel.CLEAN_GREEN VISIBLE NONE;\
        OlderTaxParcel.HEATSYS OlderTaxParcel.HEATSYS VISIBLE NONE;\
        OlderTaxParcel.FUEL OlderTaxParcel.FUEL VISIBLE NONE;\
        OlderTaxParcel.UTILITY OlderTaxParcel.UTILITY VISIBLE NONE;\
        OlderTaxParcel.APRLAND OlderTaxParcel.APRLAND VISIBLE NONE;\
        OlderTaxParcel.APRBLDG OlderTaxParcel.APRBLDG VISIBLE NONE;\
        OlderTaxParcel.APRTOTAL OlderTaxParcel.APRTOTAL VISIBLE NONE;\
        OlderTaxParcel.SALEDT OlderTaxParcel.SALEDT VISIBLE NONE;\
        OlderTaxParcel.PRICE OlderTaxParcel.PRICE VISIBLE NONE;\
        OlderTaxParcel.PREV_PRICE OlderTaxParcel.PREV_PRICE VISIBLE NONE;\
        OlderTaxParcel.SCHOOL_DIS OlderTaxParcel.SCHOOL_DIS VISIBLE NONE;\
        OlderTaxParcel.COMM_STRUC OlderTaxParcel.COMM_STRUC VISIBLE NONE;\
        OlderTaxParcel.COMM_YEAR_BUILT OlderTaxParcel.COMM_YEAR_BUILT VISIBLE NONE;\
        OlderTaxParcel.COMM_BUILDING_SQ_FT OlderTaxParcel.COMM_BUILDING_SQ_FT VISIBLE NONE;\
        OlderTaxParcel.GRADE OlderTaxParcel.GRADE VISIBLE NONE;\
        OlderTaxParcel.CDU OlderTaxParcel.CDU VISIBLE NONE;\
        OlderTaxParcel.DIST_NEW OlderTaxParcel.DIST_NEW VISIBLE NONE;\
        OlderTaxParcel.MUNICIPAL OlderTaxParcel.MUNICIPAL VISIBLE NONE;\
        OlderTaxParcel.SCHOOL OlderTaxParcel.SCHOOL VISIBLE NONE;\
        OlderTaxParcel.COUNTY OlderTaxParcel.COUNTY VISIBLE NONE;\
        OlderTaxParcel.Muni_Tax_Total OlderTaxParcel.Muni_Tax_Total VISIBLE NONE;\
        OlderTaxParcel.School_Tax_Total OlderTaxParcel.School_Tax_Total VISIBLE NONE;\
        OlderTaxParcel.County_Tax_Total OlderTaxParcel.County_Tax_Total VISIBLE NONE;\
        OlderTaxParcel.Total_Tax OlderTaxParcel.Total_Tax VISIBLE NONE;\
        OlderTaxParcel.TAX1 OlderTaxParcel.TAX1 VISIBLE NONE;\
        OlderTaxParcel.TAX2 OlderTaxParcel.TAX2 VISIBLE NONE;\
        OlderTaxParcel.TAX3 OlderTaxParcel.TAX3 VISIBLE NONE;\
        OlderTaxParcel.TAX4 OlderTaxParcel.TAX4 VISIBLE NONE;\
        OlderTaxParcel.TAX5 OlderTaxParcel.TAX5 VISIBLE NONE;\
        OlderTaxParcel.OTHER_TAX OlderTaxParcel.OTHER_TAX VISIBLE NONE;\
        OlderTaxParcel.ABTYPE OlderTaxParcel.ABTYPE VISIBLE NONE;\
        OlderTaxParcel.FACE_TOTAL OlderTaxParcel.FACE_TOTAL VISIBLE NONE;\
        OlderTaxParcel.ABTYPE_1 OlderTaxParcel.ABTYPE_1 VISIBLE NONE;\
        OlderTaxParcel.FACE_TOTAL_1 OlderTaxParcel.FACE_TOTAL_1 VISIBLE NONE;\
        OlderTaxParcel.HOMESTEAD OlderTaxParcel.HOMESTEAD VISIBLE NONE;\
        OlderTaxParcel.FARMSTEAD OlderTaxParcel.FARMSTEAD VISIBLE NONE;\
        OlderTaxParcel.PROGRAM OlderTaxParcel.PROGRAM VISIBLE NONE;\
        OlderTaxParcel.Shape_Length OlderTaxParcel.Shape_Length VISIBLE NONE;\
        OlderTaxParcel.Shape_Area OlderTaxParcel.Shape_Area VISIBLE NONE")

        # message (report, "Selecting Parcel that Attributes are different from {} and {}\n".format(os.path.join(DataDriven_Workplace,"RecentTaxParcel"),os.path.join(DataDriven_Workplace,"OlderTaxParcel")))
        # Step Selects Features from RecentTaxParcel_Attributes Feature Layer that:
        # Owner, Property Address, LUC, Homestead, Farmstead, Class, Tax District, Total Apprial, Sale Date or School District do not match
        arcpy.SelectLayerByAttribute_management("RecentTaxParcel_Attributes", "NEW_SELECTION", "RecentTaxParcel.OWNER_FULL <> OlderTaxParcel.OWNER_FULL OR RecentTaxParcel.PROPADR <> OlderTaxParcel.PROPADR OR RecentTaxParcel.LUC <> OlderTaxParcel.LUC OR RecentTaxParcel.CLASS <> OlderTaxParcel.CLASS OR RecentTaxParcel.DIST_NEW <> OlderTaxParcel.DIST_NEW OR RecentTaxParcel.APRTOTAL <> OlderTaxParcel.APRTOTAL OR RecentTaxParcel.SALEDT <> OlderTaxParcel.SALEDT OR RecentTaxParcel.SCHOOL_DIS <> OlderTaxParcel.SCHOOL_DIS")

        # message (report, "Selecting/Removing Parcels that have Geometry Changes from {} and {}\n".format(os.path.join(DataDriven_Workplace,"RecentTaxParcel"),os.path.join(DataDriven_Workplace,"OlderTaxParcel")))
        # Removing from Selection any properties that have geometry changes. These will be found in the find geometry change section
        arcpy.SelectLayerByAttribute_management("RecentTaxParcel_Attributes", "REMOVE_FROM_SELECTION", "RecentTaxParcel.Shape_Area <> OlderTaxParcel.Shape_Area")

        # message (report, "Creating {}\n".format(Attribute_Change))
        # Step Selects Features from RecentTaxParcel_Attributes and overwrites/copies results to Attribute_Change variable
        arcpy.Select_analysis("RecentTaxParcel_Attributes", Attribute_Change, "")

        # message (report, "Adding Field and Calculating {}\n".format(Attribute_Change))
        # Process: Add Field called Type
        arcpy.AddField_management(Attribute_Change, "Type", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

        # Process: Calculates Type Field
        arcpy.CalculateField_management(Attribute_Change, "Type", "\"Attribute Change\"", "PYTHON", "")

        # Steps used to Tabulate count of Attribute Changes in particular tax district
        message (report, "Calculating Attribute Count for {}\n".format(Attribute_Change))
        Attributeresult = Attribute_Change
        result = arcpy.GetCount_management(Attributeresult)
        count = int(result.getOutput(0))
        message (report,("Found (" + str(count) + ") Attribute Changes for Tax District {}\n".format(districts)))
        # Tabulates/Adds count information to Attribute Change For Loop
        For_Attribute_Count = For_Attribute_Count + count
        # Tabulates/Adds count information to Attribute Change For Loop
        Total_AttributeChanges = Total_AttributeChanges + count

        # Tabulates and prints out Numbers for New Parcels, Attribute Changes, and Geometry Changes for tax district
        message (report, "Total Changes for District {}\n New Parcels = (" + str(For_NewParcel_Count) + ")\n Geometry Changes = (" + str(For_Geometry_Count) + ")\n Attribute Changes = (" + str(For_Attribute_Count) + ")\n".format(districts))


####################################################   Append New Parcels, Geometry, and Attribute Changes to UpdateParcels_DataDriven    #############################################################################################################################################################################################

        # This section Appends Attribute, Geometry, and New Parcel Layers together to create UpdatedParcels_DataDriven Layer.
        # UpdatedParcels_DataDriven Layer will be the layer used to update PDFs on Web Service via DataDriven Pages
        message (report, "Appending Attribute, Geometry, and New Parcels Found to {}\n".format(os.path.join(DataDriven_Workplace,"UpdatedParcels_DataDriven")))

        # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
        # The following inputs are layers or table views: "UpdatedParcels_DataDriven"
        arcpy.Append_management(""+Attribute_Change+";"+Geometry_Change+";"+New_Parcel+"", os.path.join(DataDriven_Workplace,"UpdatedParcels_DataDriven"), "NO_TEST",\
         "RecentTaxParcel_PIDN_LEASE \"PIDN_LEASE\" true true false 18 Text 0 0 ,First,#,"+New_Parcel+",PIDN_LEASE,-1,-1,"+Attribute_Change+",RecentTaxParcel_PIDN_LEASE,-1,-1,"+Geometry_Change+",RecentTaxParcel_PIDN_LEASE,-1,-1;\
         RecentTaxParcel_PIDN_LEASE_1 \"PIDN_LEASE\" true true false 18 Text 0 0 ,First,#,"+New_Parcel+",PIDN_LEASE_1,-1,-1,"+Attribute_Change+",RecentTaxParcel_PIDN_LEASE_1,-1,-1,"+Geometry_Change+",RecentTaxParcel_PIDN_LEASE_1,-1,-1;\
         RecentTaxParcel_PIDN \"PIDN\" true true false 13 Text 0 0 ,First,#,"+New_Parcel+",PIDN,-1,-1,"+Attribute_Change+",RecentTaxParcel_PIDN,-1,-1,"+Geometry_Change+",RecentTaxParcel_PIDN,-1,-1;\
         RecentTaxParcel_DEED_BK \"DEED_BK\" true true false 8 Text 0 0 ,First,#,"+New_Parcel+",DEED_BK,-1,-1,"+Attribute_Change+",RecentTaxParcel_DEED_BK,-1,-1,"+Geometry_Change+",RecentTaxParcel_DEED_BK,-1,-1;\
         RecentTaxParcel_DEED_PG \"DEED_PG\" true true false 8 Text 0 0 ,First,#,"+New_Parcel+",DEED_PG,-1,-1,"+Attribute_Change+",RecentTaxParcel_DEED_PG,-1,-1,"+Geometry_Change+",RecentTaxParcel_DEED_PG,-1,-1;\
         RecentTaxParcel_PROPADR \"PROPADR\" true true false 54 Text 0 0 ,First,#,"+New_Parcel+",PROPADR,-1,-1,"+Attribute_Change+",RecentTaxParcel_PROPADR,-1,-1,"+Geometry_Change+",RecentTaxParcel_PROPADR,-1,-1;\
         RecentTaxParcel_OWNER_FULL \"OWNER_FULL\" true true false 81 Text 0 0 ,First,#,"+New_Parcel+",OWNER_FULL,-1,-1,"+Attribute_Change+",RecentTaxParcel_OWNER_FULL,-1,-1,"+Geometry_Change+",RecentTaxParcel_OWNER_FULL,-1,-1;\
         RecentTaxParcel_OWN_NAME1 \"OWN_NAME1\" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",OWN_NAME1,-1,-1,"+Attribute_Change+",RecentTaxParcel_OWN_NAME1,-1,-1,"+Geometry_Change+",RecentTaxParcel_OWN_NAME1,-1,-1;\
         RecentTaxParcel_OWN_NAME2 \"OWN_NAME2\" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",OWN_NAME2,-1,-1,"+Attribute_Change+",RecentTaxParcel_OWN_NAME2,-1,-1,"+Geometry_Change+",RecentTaxParcel_OWN_NAME2,-1,-1;\
         RecentTaxParcel_MAIL_ADDR_FULL \"MAIL_ADDR_FULL\" true true false 124 Text 0 0 ,First,#,"+New_Parcel+",MAIL_ADDR_FULL,-1,-1,"+Attribute_Change+",RecentTaxParcel_MAIL_ADDR_FULL,-1,-1,"+Geometry_Change+",RecentTaxParcel_MAIL_ADDR_FULL,-1,-1;\
         RecentTaxParcel_MAIL_ADDR1 \"MAIL_ADDR1\" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",MAIL_ADDR1,-1,-1,"+Attribute_Change+",RecentTaxParcel_MAIL_ADDR1,-1,-1,"+Geometry_Change+",RecentTaxParcel_MAIL_ADDR1,-1,-1;\
         RecentTaxParcel_MAIL_ADDR2 \"MAIL_ADDR2\" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",MAIL_ADDR2,-1,-1,"+Attribute_Change+",RecentTaxParcel_MAIL_ADDR2,-1,-1,"+Geometry_Change+",RecentTaxParcel_MAIL_ADDR2,-1,-1;\
         RecentTaxParcel_MAIL_ADDR3 \"MAIL_ADDR3\" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",MAIL_ADDR3,-1,-1,"+Attribute_Change+",RecentTaxParcel_MAIL_ADDR3,-1,-1,"+Geometry_Change+",RecentTaxParcel_MAIL_ADDR3,-1,-1;\
         RecentTaxParcel_PREV_OWNER \"PREV_OWNER\" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",PREV_OWNER,-1,-1,"+Attribute_Change+",RecentTaxParcel_PREV_OWNER,-1,-1,"+Geometry_Change+",RecentTaxParcel_PREV_OWNER,-1,-1;\
         RecentTaxParcel_CLASS \"CLASS\" true true false 1 Text 0 0 ,First,#,"+New_Parcel+",CLASS,-1,-1,"+Attribute_Change+",RecentTaxParcel_CLASS,-1,-1,"+Geometry_Change+",RecentTaxParcel_CLASS,-1,-1;\
         RecentTaxParcel_LUC \"LUC\" true true false 4 Text 0 0 ,First,#,"+New_Parcel+",LUC,-1,-1,"+Attribute_Change+",RecentTaxParcel_LUC,-1,-1,"+Geometry_Change+",RecentTaxParcel_LUC,-1,-1;\
         RecentTaxParcel_ACRES \"ACRES\" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",ACRES,-1,-1,"+Attribute_Change+",RecentTaxParcel_ACRES,-1,-1,"+Geometry_Change+",RecentTaxParcel_ACRES,-1,-1;\
         RecentTaxParcel_STYLE \"STYLE\" true true false 2 Text 0 0 ,First,#,"+New_Parcel+",STYLE,-1,-1,"+Attribute_Change+",RecentTaxParcel_STYLE,-1,-1,"+Geometry_Change+",RecentTaxParcel_STYLE,-1,-1;\
         RecentTaxParcel_NUM_STORIE \"NUM_STORIE\" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",NUM_STORIE,-1,-1,"+Attribute_Change+",RecentTaxParcel_NUM_STORIE,-1,-1,"+Geometry_Change+",RecentTaxParcel_NUM_STORIE,-1,-1;\
         RecentTaxParcel_RES_LIVING_AREA \"RES_LIVING_ARE\" true true false 4 Long 0 0 ,First,#,"+New_Parcel+",RES_LIVING_AREA,-1,-1,"+Attribute_Change+",RecentTaxParcel_RES_LIVING_AREA,-1,-1,"+Geometry_Change+",RecentTaxParcel_RES_LIVING_AREA,-1,-1;\
         RecentTaxParcel_YRBLT \"YRBLT\" true true false 2 Short 0 0 ,First,#,"+New_Parcel+",YRBLT,-1,-1,"+Attribute_Change+",RecentTaxParcel_YRBLT,-1,-1,"+Geometry_Change+",RecentTaxParcel_YRBLT,-1,-1;\
         RecentTaxParcel_CLEAN_GREEN \"CLEAN_GREEN\" true true false 3 Text 0 0 ,First,#,"+New_Parcel+",CLEAN_GREEN,-1,-1,"+Attribute_Change+",RecentTaxParcel_CLEAN_GREEN,-1,-1,"+Geometry_Change+",RecentTaxParcel_CLEAN_GREEN,-1,-1;\
         RecentTaxParcel_HEATSYS \"HEATSYS\" true true false 2 Short 0 0 ,First,#,"+New_Parcel+",HEATSYS,-1,-1,"+Attribute_Change+",RecentTaxParcel_HEATSYS,-1,-1,"+Geometry_Change+",RecentTaxParcel_HEATSYS,-1,-1;\
         RecentTaxParcel_FUEL \"FUEL\" true true false 2 Short 0 0 ,First,#,"+New_Parcel+",FUEL,-1,-1,"+Attribute_Change+",RecentTaxParcel_FUEL,-1,-1,"+Geometry_Change+",RecentTaxParcel_FUEL,-1,-1;\
         RecentTaxParcel_UTILITY \"UTILITY\" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",UTILITY,-1,-1,"+Attribute_Change+",RecentTaxParcel_UTILITY,-1,-1,"+Geometry_Change+",RecentTaxParcel_UTILITY,-1,-1;\
         RecentTaxParcel_APRLAND \"APRLAND\" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",APRLAND,-1,-1,"+Attribute_Change+",RecentTaxParcel_APRLAND,-1,-1,"+Geometry_Change+",RecentTaxParcel_APRLAND,-1,-1;\
         RecentTaxParcel_APRBLDG \"APRBLDG \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",APRBLDG,-1,-1,"+Attribute_Change+",RecentTaxParcel_APRBLDG,-1,-1,"+Geometry_Change+",RecentTaxParcel_APRBLDG,-1,-1;\
         RecentTaxParcel_APRTOTAL \"APRTOTAL \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",APRTOTAL,-1,-1,"+Attribute_Change+",RecentTaxParcel_APRTOTAL,-1,-1,"+Geometry_Change+",RecentTaxParcel_APRTOTAL,-1,-1;\
         RecentTaxParcel_SALEDT \"SALEDT \" true true false 11 Text 0 0 ,First,#,"+New_Parcel+",SALEDT,-1,-1,"+Attribute_Change+",RecentTaxParcel_SALEDT,-1,-1,"+Geometry_Change+",RecentTaxParcel_SALEDT,-1,-1;\
         RecentTaxParcel_PRICE \"PRICE \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",PRICE,-1,-1,"+Attribute_Change+",RecentTaxParcel_PRICE,-1,-1,"+Geometry_Change+",RecentTaxParcel_PRICE,-1,-1;\
         RecentTaxParcel_PREV_PRICE \"PREV_PRICE \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",PREV_PRICE,-1,-1,"+Attribute_Change+",RecentTaxParcel_PREV_PRICE,-1,-1,"+Geometry_Change+",RecentTaxParcel_PREV_PRICE,-1,-1;\
         RecentTaxParcel_SCHOOL_DIS \"SCHOOL_DIS \" true true false 5 Text 0 0 ,First,#,"+New_Parcel+",SCHOOL_DIS,-1,-1,"+Attribute_Change+",RecentTaxParcel_SCHOOL_DIS,-1,-1,"+Geometry_Change+",RecentTaxParcel_SCHOOL_DIS,-1,-1;\
         RecentTaxParcel_COMM_STRUC \"COMM_STRUC \" true true false 3 Text 0 0 ,First,#,"+New_Parcel+",COMM_STRUC,-1,-1,"+Attribute_Change+",RecentTaxParcel_COMM_STRUC,-1,-1,"+Geometry_Change+",RecentTaxParcel_COMM_STRUC,-1,-1;\
         RecentTaxParcel_COMM_YEAR_BUILT \"COMM_YEAR_BUILT \" true true false 4 Long 0 0 ,First,#,"+New_Parcel+",COMM_YEAR_BUILT,-1,-1,"+Attribute_Change+",RecentTaxParcel_COMM_YEAR_BUILT,-1,-1,"+Geometry_Change+",RecentTaxParcel_COMM_YEAR_BUILT,-1,-1;\
         RecentTaxParcel_COMM_BUILDING_SQ_FT \"COMM_BUILDING_SQ_FT \" true true false 4 Long 0 0 ,First,#,"+New_Parcel+",COMM_BUILDING_SQ_FT,-1,-1,"+Attribute_Change+",RecentTaxParcel_COMM_BUILDING_SQ_FT,-1,-1,"+Geometry_Change+",RecentTaxParcel_COMM_BUILDING_SQ_FT,-1,-1;\
         RecentTaxParcel_GRADE \"GRADE \" true true false 2 Text 0 0 ,First,#,"+New_Parcel+",GRADE,-1,-1,"+Attribute_Change+",RecentTaxParcel_GRADE,-1,-1,"+Geometry_Change+",RecentTaxParcel_GRADE,-1,-1;\
         RecentTaxParcel_CDU \"CDU \" true true false 2 Text 0 0 ,First,#,"+New_Parcel+",CDU,-1,-1,"+Attribute_Change+",RecentTaxParcel_CDU,-1,-1,"+Geometry_Change+",RecentTaxParcel_CDU,-1,-1;\
         RecentTaxParcel_DIST_NEW \"DIST_NEW \" true true false 3 Text 0 0 ,First,#,"+New_Parcel+",DIST_NEW,-1,-1,"+Attribute_Change+",RecentTaxParcel_DIST_NEW,-1,-1,"+Geometry_Change+",RecentTaxParcel_DIST_NEW,-1,-1;\
         RecentTaxParcel_MUNICIPAL \"MUNICIPAL \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",MUNICIPAL,-1,-1,"+Attribute_Change+",RecentTaxParcel_MUNICIPAL,-1,-1,"+Geometry_Change+",RecentTaxParcel_MUNICIPAL,-1,-1;\
         RecentTaxParcel_SCHOOL \"SCHOOL \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",SCHOOL,-1,-1,"+Attribute_Change+",RecentTaxParcel_SCHOOL,-1,-1,"+Geometry_Change+",RecentTaxParcel_SCHOOL,-1,-1;\
         RecentTaxParcel_COUNTY \"COUNTY \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",COUNTY,-1,-1,"+Attribute_Change+",RecentTaxParcel_COUNTY,-1,-1,"+Geometry_Change+",RecentTaxParcel_COUNTY,-1,-1;\
         RecentTaxParcel_Muni_Tax_Total \"Muni_Tax_Total \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",Muni_Tax_Total,-1,-1,"+Attribute_Change+",RecentTaxParcel_Muni_Tax_Total,-1,-1,"+Geometry_Change+",RecentTaxParcel_Muni_Tax_Total,-1,-1;\
         RecentTaxParcel_School_Tax_Total \"School_Tax_Total \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",School_Tax_Total,-1,-1,"+Attribute_Change+",RecentTaxParcel_School_Tax_Total,-1,-1,"+Geometry_Change+",RecentTaxParcel_School_Tax_Total,-1,-1;\
         RecentTaxParcel_County_Tax_Total \"County_Tax_Total \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",County_Tax_Total,-1,-1,"+Attribute_Change+",RecentTaxParcel_County_Tax_Total,-1,-1,"+Geometry_Change+",RecentTaxParcel_County_Tax_Total,-1,-1;\
         RecentTaxParcel_Total_Tax \"Total_Tax \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",Total_Tax,-1,-1,"+Attribute_Change+",RecentTaxParcel_Total_Tax,-1,-1,"+Geometry_Change+",RecentTaxParcel_Total_Tax,-1,-1;\
         RecentTaxParcel_TAX1 \"TAX1 \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",TAX1,-1,-1,"+Attribute_Change+",RecentTaxParcel_TAX1,-1,-1,"+Geometry_Change+",RecentTaxParcel_TAX1,-1,-1;\
         RecentTaxParcel_TAX2 \"TAX2 \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",TAX2,-1,-1,"+Attribute_Change+",RecentTaxParcel_TAX2,-1,-1,"+Geometry_Change+",RecentTaxParcel_TAX2,-1,-1;\
         RecentTaxParcel_TAX3 \"TAX3 \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",TAX3,-1,-1,"+Attribute_Change+",RecentTaxParcel_TAX3,-1,-1,"+Geometry_Change+",RecentTaxParcel_TAX3,-1,-1;\
         RecentTaxParcel_TAX4 \"TAX4 \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",TAX4,-1,-1,"+Attribute_Change+",RecentTaxParcel_TAX4,-1,-1,"+Geometry_Change+",RecentTaxParcel_TAX4,-1,-1;\
         RecentTaxParcel_TAX5 \"TAX5 \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",TAX5,-1,-1,"+Attribute_Change+",RecentTaxParcel_TAX5,-1,-1,"+Geometry_Change+",RecentTaxParcel_TAX5,-1,-1;\
         RecentTaxParcel_OTHER_TAX \"OTHER_TAX \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",OTHER_TAX,-1,-1,"+Attribute_Change+",RecentTaxParcel_OTHER_TAX,-1,-1,"+Geometry_Change+",RecentTaxParcel_OTHER_TAX,-1,-1;\
         RecentTaxParcel_ABTYPE \"ABTYPE \" true true false 254 Text 0 0 ,First,#,"+New_Parcel+",ABTYPE,-1,-1,"+Attribute_Change+",RecentTaxParcel_ABTYPE,-1,-1,"+Geometry_Change+",RecentTaxParcel_ABTYPE,-1,-1;\
         RecentTaxParcel_FACE_TOTAL \"FACE_TOTAL \" true true false 50 Text 0 0 ,First,#,"+New_Parcel+",FACE_TOTAL,-1,-1,"+Attribute_Change+",RecentTaxParcel_FACE_TOTAL,-1,-1,"+Geometry_Change+",RecentTaxParcel_FACE_TOTAL,-1,-1;\
         RecentTaxParcel_ABTYPE_1 \"ABTYPE_1 \" true true false 254 Text 0 0 ,First,#,"+New_Parcel+",ABTYPE_1,-1,-1,"+Attribute_Change+",RecentTaxParcel_ABTYPE_1,-1,-1,"+Geometry_Change+",RecentTaxParcel_ABTYPE_1,-1,-1;\
         RecentTaxParcel_FACE_TOTAL_1 \"FACE_TOTAL_1 \" true true false 50 Text 0 0 ,First,#,"+New_Parcel+",FACE_TOTAL_1,-1,-1,"+Attribute_Change+",RecentTaxParcel_FACE_TOTAL_1,-1,-1,"+Geometry_Change+",RecentTaxParcel_FACE_TOTAL_1,-1,-1;\
         RecentTaxParcel_HOMESTEAD \"HOMESTEAD \" true true false 3 Text 0 0 ,First,#,"+New_Parcel+",HOMESTEAD,-1,-1,"+Attribute_Change+",RecentTaxParcel_HOMESTEAD,-1,-1,"+Geometry_Change+",RecentTaxParcel_HOMESTEAD,-1,-1;\
         RecentTaxParcel_FARMSTEAD \"FARMSTEAD \" true true false 3 Text 0 0 ,First,#,"+New_Parcel+",FARMSTEAD,-1,-1,"+Attribute_Change+",RecentTaxParcel_FARMSTEAD,-1,-1,"+Geometry_Change+",RecentTaxParcel_FARMSTEAD,-1,-1;\
         RecentTaxParcel_PROGRAM \"PROGRAM \" true true false 255 Text 0 0 ,First,#,"+New_Parcel+",PROGRAM,-1,-1,"+Attribute_Change+",RecentTaxParcel_PROGRAM,-1,-1,"+Geometry_Change+",RecentTaxParcel_PROGRAM,-1,-1;\
         OlderTaxParcel_OBJECTID \"OBJECTID \" true true false 4 Long 0 0 ,First,#,"+Attribute_Change+",OlderTaxParcel_OBJECTID,-1,-1,"+Geometry_Change+",OlderTaxParcel_OBJECTID,-1,-1;\
         OlderTaxParcel_PIDN_LEASE \"PIDN_LEASE \" true true false 18 Text 0 0 ,First,#,"+New_Parcel+",PIDN_LEASE_12,-1,-1,"+Attribute_Change+",OlderTaxParcel_PIDN_LEASE,-1,-1,"+Geometry_Change+",OlderTaxParcel_PIDN_LEASE,-1,-1;\
         OlderTaxParcel_PIDN_LEASE_1 \"PIDN_LEASE \" true true false 18 Text 0 0 ,First,#,"+New_Parcel+",PIDN_LEASE_12_13,-1,-1,"+Attribute_Change+",OlderTaxParcel_PIDN_LEASE_1,-1,-1,"+Geometry_Change+",OlderTaxParcel_PIDN_LEASE_1,-1,-1;\
         OlderTaxParcel_PIDN \"PIDN \" true true false 13 Text 0 0 ,First,#,"+New_Parcel+",PIDN_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_PIDN,-1,-1,"+Geometry_Change+",OlderTaxParcel_PIDN,-1,-1;\
         OlderTaxParcel_DEED_BK \"DEED_BK \" true true false 8 Text 0 0 ,First,#,"+New_Parcel+",DEED_BK_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_DEED_BK,-1,-1,"+Geometry_Change+",OlderTaxParcel_DEED_BK,-1,-1;\
         OlderTaxParcel_DEED_PG \"DEED_PG \" true true false 8 Text 0 0 ,First,#,"+New_Parcel+",DEED_PG_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_DEED_PG,-1,-1,"+Geometry_Change+",OlderTaxParcel_DEED_PG,-1,-1;\
         OlderTaxParcel_PROPADR \"PROPADR \" true true false 54 Text 0 0 ,First,#,"+New_Parcel+",PROPADR_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_PROPADR,-1,-1,"+Geometry_Change+",OlderTaxParcel_PROPADR,-1,-1;\
         OlderTaxParcel_OWNER_FULL \"OWNER_FULL \" true true false 81 Text 0 0 ,First,#,"+New_Parcel+",OWNER_FULL_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_OWNER_FULL,-1,-1,"+Geometry_Change+",OlderTaxParcel_OWNER_FULL,-1,-1;\
         OlderTaxParcel_OWN_NAME1 \"OWN_NAME1 \" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",OWN_NAME1_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_OWN_NAME1,-1,-1,"+Geometry_Change+",OlderTaxParcel_OWN_NAME1,-1,-1;\
         OlderTaxParcel_OWN_NAME2 \"OWN_NAME2 \" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",OWN_NAME2_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_OWN_NAME2,-1,-1,"+Geometry_Change+",OlderTaxParcel_OWN_NAME2,-1,-1;\
         OlderTaxParcel_MAIL_ADDR_FULL \"MAIL_ADDR_FULL \" true true false 124 Text 0 0 ,First,#,"+New_Parcel+",MAIL_ADDR_FULL_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_MAIL_ADDR_FULL,-1,-1,"+Geometry_Change+",OlderTaxParcel_MAIL_ADDR_FULL,-1,-1;\
         OlderTaxParcel_MAIL_ADDR1 \"MAIL_ADDR1 \" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",MAIL_ADDR1_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_MAIL_ADDR1,-1,-1,"+Geometry_Change+",OlderTaxParcel_MAIL_ADDR1,-1,-1;\
         OlderTaxParcel_MAIL_ADDR2 \"MAIL_ADDR2 \" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",MAIL_ADDR2_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_MAIL_ADDR2,-1,-1,"+Geometry_Change+",OlderTaxParcel_MAIL_ADDR2,-1,-1;\
         OlderTaxParcel_MAIL_ADDR3 \"MAIL_ADDR3 \" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",MAIL_ADDR3_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_MAIL_ADDR3,-1,-1,"+Geometry_Change+",OlderTaxParcel_MAIL_ADDR3,-1,-1;\
         OlderTaxParcel_PREV_OWNER \"PREV_OWNER \" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",PREV_OWNER_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_PREV_OWNER,-1,-1,"+Geometry_Change+",OlderTaxParcel_PREV_OWNER,-1,-1;\
         OlderTaxParcel_CLASS \"CLASS \" true true false 1 Text 0 0 ,First,#,"+New_Parcel+",CLASS_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_CLASS,-1,-1,"+Geometry_Change+",OlderTaxParcel_CLASS,-1,-1;\
         OlderTaxParcel_LUC \"LUC \" true true false 4 Text 0 0 ,First,#,"+New_Parcel+",LUC_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_LUC,-1,-1,"+Geometry_Change+",OlderTaxParcel_LUC,-1,-1;\
         OlderTaxParcel_ACRES \"ACRES \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",ACRES_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_ACRES,-1,-1,"+Geometry_Change+",OlderTaxParcel_ACRES,-1,-1;\
         OlderTaxParcel_STYLE \"STYLE \" true true false 2 Text 0 0 ,First,#,"+New_Parcel+",STYLE_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_STYLE,-1,-1,"+Geometry_Change+",OlderTaxParcel_STYLE,-1,-1;\
         OlderTaxParcel_NUM_STORIE \"NUM_STORIE \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",NUM_STORIE_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_NUM_STORIE,-1,-1,"+Geometry_Change+",OlderTaxParcel_NUM_STORIE,-1,-1;\
         OlderTaxParcel_RES_LIVING_AREA \"RES_LIVING_AREA \" true true false 4 Long 0 0 ,First,#,"+New_Parcel+",RES_LIVING_AREA_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_RES_LIVING_AREA,-1,-1,"+Geometry_Change+",OlderTaxParcel_RES_LIVING_AREA,-1,-1;\
         OlderTaxParcel_YRBLT \"YRBLT \" true true false 2 Short 0 0 ,First,#,"+New_Parcel+",YRBLT_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_YRBLT,-1,-1,"+Geometry_Change+",OlderTaxParcel_YRBLT,-1,-1;\
         OlderTaxParcel_CLEAN_GREEN \"CLEAN_GREEN \" true true false 3 Text 0 0 ,First,#,"+New_Parcel+",CLEAN_GREEN_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_CLEAN_GREEN,-1,-1,"+Geometry_Change+",OlderTaxParcel_CLEAN_GREEN,-1,-1;\
         OlderTaxParcel_HEATSYS \"HEATSYS \" true true false 2 Short 0 0 ,First,#,"+New_Parcel+",HEATSYS_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_HEATSYS,-1,-1,"+Geometry_Change+",OlderTaxParcel_HEATSYS,-1,-1;\
         OlderTaxParcel_FUEL \"FUEL \" true true false 2 Short 0 0 ,First,#,"+New_Parcel+",FUEL_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_FUEL,-1,-1,"+Geometry_Change+",OlderTaxParcel_FUEL,-1,-1;\
         OlderTaxParcel_UTILITY \"UTILITY \" true true false 40 Text 0 0 ,First,#,"+New_Parcel+",UTILITY_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_UTILITY,-1,-1,"+Geometry_Change+",OlderTaxParcel_UTILITY,-1,-1;\
         OlderTaxParcel_APRLAND \"APRLAND \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",APRLAND_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_APRLAND,-1,-1,"+Geometry_Change+",OlderTaxParcel_APRLAND,-1,-1;\
         OlderTaxParcel_APRBLDG \"APRBLDG \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",APRBLDG_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_APRBLDG,-1,-1,"+Geometry_Change+",OlderTaxParcel_APRBLDG,-1,-1;\
         OlderTaxParcel_APRTOTAL \"APRTOTAL \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",APRTOTAL_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_APRTOTAL,-1,-1,"+Geometry_Change+",OlderTaxParcel_APRTOTAL,-1,-1;\
         OlderTaxParcel_SALEDT \"SALEDT \" true true false 11 Text 0 0 ,First,#,"+New_Parcel+",SALEDT_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_SALEDT,-1,-1,"+Geometry_Change+",OlderTaxParcel_SALEDT,-1,-1;\
         OlderTaxParcel_PRICE \"PRICE \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",PRICE_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_PRICE,-1,-1,"+Geometry_Change+",OlderTaxParcel_PRICE,-1,-1;\
         OlderTaxParcel_PREV_PRICE \"PREV_PRICE \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",PREV_PRICE_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_PREV_PRICE,-1,-1,"+Geometry_Change+",OlderTaxParcel_PREV_PRICE,-1,-1;\
         OlderTaxParcel_SCHOOL_DIS \"SCHOOL_DIS \" true true false 5 Text 0 0 ,First,#,"+New_Parcel+",SCHOOL_DIS_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_SCHOOL_DIS,-1,-1,"+Geometry_Change+",OlderTaxParcel_SCHOOL_DIS,-1,-1;\
         OlderTaxParcel_COMM_STRUC \"COMM_STRUC \" true true false 3 Text 0 0 ,First,#,"+New_Parcel+",COMM_STRUC_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_COMM_STRUC,-1,-1,"+Geometry_Change+",OlderTaxParcel_COMM_STRUC,-1,-1;\
         OlderTaxParcel_COMM_YEAR_BUILT \"COMM_YEAR_BUILT \" true true false 4 Long 0 0 ,First,#,"+New_Parcel+",COMM_YEAR_BUILT_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_COMM_YEAR_BUILT,-1,-1,"+Geometry_Change+",OlderTaxParcel_COMM_YEAR_BUILT,-1,-1;\
         OlderTaxParcel_COMM_BUILDING_SQ_FT \"COMM_BUILDING_SQ_FT \" true true false 4 Long 0 0 ,First,#,"+New_Parcel+",COMM_BUILDING_SQ_FT_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_COMM_BUILDING_SQ_FT,-1,-1,"+Geometry_Change+",OlderTaxParcel_COMM_BUILDING_SQ_FT,-1,-1;\
         OlderTaxParcel_GRADE \"GRADE \" true true false 2 Text 0 0 ,First,#,"+New_Parcel+",GRADE_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_GRADE,-1,-1,"+Geometry_Change+",OlderTaxParcel_GRADE,-1,-1;\
         OlderTaxParcel_CDU \"CDU \" true true false 2 Text 0 0 ,First,#,"+New_Parcel+",CDU_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_CDU,-1,-1,"+Geometry_Change+",OlderTaxParcel_CDU,-1,-1;\
         OlderTaxParcel_DIST_NEW \"DIST_NEW \" true true false 3 Text 0 0 ,First,#,"+New_Parcel+",DIST_NEW_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_DIST_NEW,-1,-1,"+Geometry_Change+",OlderTaxParcel_DIST_NEW,-1,-1;\
         OlderTaxParcel_MUNICIPAL \"MUNICIPAL \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",MUNICIPAL_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_MUNICIPAL,-1,-1,"+Geometry_Change+",OlderTaxParcel_MUNICIPAL,-1,-1;\
         OlderTaxParcel_SCHOOL \"SCHOOL \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",SCHOOL_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_SCHOOL,-1,-1,"+Geometry_Change+",OlderTaxParcel_SCHOOL,-1,-1;\
         OlderTaxParcel_COUNTY \"COUNTY \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",COUNTY_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_COUNTY,-1,-1,"+Geometry_Change+",OlderTaxParcel_COUNTY,-1,-1;\
         OlderTaxParcel_Muni_Tax_Total \"Muni_Tax_Total \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",Muni_Tax_Total_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_Muni_Tax_Total,-1,-1,"+Geometry_Change+",OlderTaxParcel_Muni_Tax_Total,-1,-1;\
         OlderTaxParcel_School_Tax_Total \"School_Tax_Total \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",School_Tax_Total_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_School_Tax_Total,-1,-1,"+Geometry_Change+",OlderTaxParcel_School_Tax_Total,-1,-1;\
         OlderTaxParcel_County_Tax_Total \"County_Tax_Total \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",County_Tax_Total,-1,-1,"+Attribute_Change+",OlderTaxParcel_County_Tax_Total,-1,-1,"+Geometry_Change+",OlderTaxParcel_County_Tax_Total,-1,-1;\
         OlderTaxParcel_Total_Tax \"Total_Tax \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",Total_Tax,-1,-1,"+Attribute_Change+",OlderTaxParcel_Total_Tax,-1,-1,"+Geometry_Change+",OlderTaxParcel_Total_Tax,-1,-1;\
         OlderTaxParcel_TAX1 \"TAX1 \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",TAX1_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_TAX1,-1,-1,"+Geometry_Change+",OlderTaxParcel_TAX1,-1,-1;\
         OlderTaxParcel_TAX2 \"TAX2 \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",TAX2_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_TAX2,-1,-1,"+Geometry_Change+",OlderTaxParcel_TAX2,-1,-1;\
         OlderTaxParcel_TAX3 \"TAX3 \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",TAX3_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_TAX3,-1,-1,"+Geometry_Change+",OlderTaxParcel_TAX3,-1,-1;\
         OlderTaxParcel_TAX4 \"TAX4 \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",TAX4_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_TAX4,-1,-1,"+Geometry_Change+",OlderTaxParcel_TAX4,-1,-1;\
         OlderTaxParcel_TAX5 \"TAX5 \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",TAX5_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_TAX5,-1,-1,"+Geometry_Change+",OlderTaxParcel_TAX5,-1,-1;\
         OlderTaxParcel_OTHER_TAX \"OTHER_TAX \" true true false 8 Double 0 0 ,First,#,"+New_Parcel+",OTHER_TAX_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_OTHER_TAX,-1,-1,"+Geometry_Change+",OlderTaxParcel_OTHER_TAX,-1,-1;\
         OlderTaxParcel_ABTYPE \"ABTYPE \" true true false 254 Text 0 0 ,First,#,"+New_Parcel+",ABTYPE_12,-1,-1,"+Attribute_Change+",OlderTaxParcel_ABTYPE,-1,-1,"+Geometry_Change+",OlderTaxParcel_ABTYPE,-1,-1;\
         OlderTaxParcel_FACE_TOTAL \"FACE_TOTAL \" true true false 50 Text 0 0 ,First,#,"+New_Parcel+",FACE_TOTAL_12,-1,-1,"+Attribute_Change+",OlderTaxParcel_FACE_TOTAL,-1,-1,"+Geometry_Change+",OlderTaxParcel_FACE_TOTAL,-1,-1;\
         OlderTaxParcel_ABTYPE_1 \"ABTYPE_1 \" true true false 254 Text 0 0 ,First,#,"+New_Parcel+",ABTYPE_12_13,-1,-1,"+Attribute_Change+",OlderTaxParcel_ABTYPE_1,-1,-1,"+Geometry_Change+",OlderTaxParcel_ABTYPE_1,-1,-1;\
         OlderTaxParcel_FACE_TOTAL_1 \"FACE_TOTAL_1 \" true true false 50 Text 0 0 ,First,#,"+New_Parcel+",FACE_TOTAL_12_13,-1,-1,"+Attribute_Change+",OlderTaxParcel_FACE_TOTAL_1,-1,-1,"+Geometry_Change+",OlderTaxParcel_FACE_TOTAL_1,-1,-1;\
         OlderTaxParcel_HOMESTEAD \"HOMESTEAD \" true true false 3 Text 0 0 ,First,#,"+New_Parcel+",HOMESTEAD_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_HOMESTEAD,-1,-1,"+Geometry_Change+",OlderTaxParcel_HOMESTEAD,-1,-1;\
         OlderTaxParcel_FARMSTEAD \"FARMSTEAD \" true true false 3 Text 0 0 ,First,#,"+New_Parcel+",FARMSTEAD_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_FARMSTEAD,-1,-1,"+Geometry_Change+",OlderTaxParcel_FARMSTEAD,-1,-1;\
         OlderTaxParcel_PROGRAM \"PROGRAM \" true true false 255 Text 0 0 ,First,#,"+New_Parcel+",PROGRAM_1,-1,-1,"+Attribute_Change+",OlderTaxParcel_PROGRAM,-1,-1,"+Geometry_Change+",OlderTaxParcel_PROGRAM,-1,-1;\
         Type \"Type \" true true false 255 Text 0 0 ,First,#,"+New_Parcel+",Type,-1,-1,"+Attribute_Change+",Type,-1,-1,"+Geometry_Change+",Type,-1,-1;\
         Shape_Length \"Shape_Length \" false true true 8 Double 0 0 ,First,#,"+New_Parcel+",Shape_Length,-1,-1,"+Attribute_Change+",Shape_Length,-1,-1,"+Geometry_Change+",Shape_Length,-1,-1;\
         Shape_Area \"Shape_Area \" false true true 8 Double 0 0 ,First,#,"+New_Parcel+",Shape_Area,-1,-1,"+Attribute_Change+",Shape_Area,-1,-1,"+Geometry_Change+",Shape_Area,-1,-1""", "")

        message (report, "Update and appending Process is complete for Tax District Number {}\n".format(districts))

        # Loop thru all Tax Districts in District List under done

    # Deletes any locks on District List
    del districts

    # Variable used to tabulate all updates from New Parcel, Geometry Changes, and Attribute Variables.
    # This Variable determines what Data Driven option will be used
    AllTotalCount = Total_NewParcel + Total_GeometryChanges + Total_AttributeChanges

    # Tabulates and prints out Total Parcel Updates plus total numbers for New Parcels, Geometry Changes and Attribute Changes
    message (report, "Total Changes:\n New Parcels = (" + str(Total_NewParcel) + ")\n Geometry Changes = (" + str(Total_GeometryChanges) + ")\n Attribute Changes = (" + str(Total_AttributeChanges) + ")\nTotal Parcel = (" + str(AllTotalCount) +")\n")

    DataDriven_Convert = os.path.join(DataDriven_Workplace,"UpdatedParcels_DataDriven")

    # Added on 02/21/2018 - Added this step because trying to run data driven pages directly from Updated Parcels Data Driven Pages continued to be unsuccessful
    # Makes a copy of Updated DataDriven Parcels and make new layer called UpdatedParcel_DataDriven_Finished.
    #This layer will be the primary layer used in the Updated Data Driven PDF process.
    message (report, "Copying UpdatedParcels_DataDriven to UpdatedParcels_DataDriven_Finished\n")
    arcpy.FeatureClassToFeatureClass_conversion(os.path.join(DataDriven_Workplace,"UpdatedParcels_DataDriven"), DataDriven_Workplace, "UpdatedParcels_DataDriven_Finished", "",\
    "RecentTaxParcel_PIDN_LEASE \"PIDN_LEASE\" true true false 18 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_PIDN_LEASE,-1,-1;\
    RecentTaxParcel_PIDN_LEASE_1 \"PIDN_LEASE\" true true false 18 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_PIDN_LEASE_1,-1,-1;\
    RecentTaxParcel_PIDN \"PIDN\" true true false 13 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_PIDN,-1,-1;\
    RecentTaxParcel_DEED_BK \"DEED_BK\" true true false 8 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_DEED_BK,-1,-1;\
    RecentTaxParcel_DEED_PG \"DEED_PG\" true true false 8 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_DEED_PG,-1,-1;\
    RecentTaxParcel_PROPADR \"PROPADR\" true true false 54 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_PROPADR,-1,-1;\
    RecentTaxParcel_OWNER_FULL \"OWNER_FULL\" true true false 81 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_OWNER_FULL,-1,-1;\
    RecentTaxParcel_OWN_NAME1 \"OWN_NAME1\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_OWN_NAME1,-1,-1;\
    RecentTaxParcel_OWN_NAME2 \"OWN_NAME2\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_OWN_NAME2,-1,-1;\
    RecentTaxParcel_MAIL_ADDR_FULL \"MAIL_ADDR_FULL\" true true false 124 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_MAIL_ADDR_FULL,-1,-1;\
    RecentTaxParcel_MAIL_ADDR1 \"MAIL_ADDR1\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_MAIL_ADDR1,-1,-1;\
    RecentTaxParcel_MAIL_ADDR2 \"MAIL_ADDR2\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_MAIL_ADDR2,-1,-1;\
    RecentTaxParcel_MAIL_ADDR3 \"MAIL_ADDR3\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_MAIL_ADDR3,-1,-1;\
    RecentTaxParcel_PREV_OWNER \"PREV_OWNER\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_PREV_OWNER,-1,-1;\
    RecentTaxParcel_CLASS \"CLASS\" true true false 1 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_CLASS,-1,-1;\
    RecentTaxParcel_LUC \"LUC\" true true false 4 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_LUC,-1,-1;\
    RecentTaxParcel_ACRES \"ACRES\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_ACRES,-1,-1;\
    RecentTaxParcel_STYLE \"STYLE\" true true false 2 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_STYLE,-1,-1;\
    RecentTaxParcel_NUM_STORIE \"NUM_STORIE\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_NUM_STORIE,-1,-1;\
    RecentTaxParcel_RES_LIVING_AREA \"RES_LIVING_ARE\" true true false 4 Long 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_RES_LIVING_AREA,-1,-1;\
    RecentTaxParcel_YRBLT \"YRBLT\" true true false 2 Short 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_YRBLT,-1,-1;\
    RecentTaxParcel_CLEAN_GREEN \"CLEAN_GREEN\" true true false 3 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_CLEAN_GREEN,-1,-1;\
    RecentTaxParcel_HEATSYS \"HEATSYS\" true true false 2 Short 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_HEATSYS,-1,-1;\
    RecentTaxParcel_FUEL \"FUEL\" true true false 2 Short 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_FUEL,-1,-1;\
    RecentTaxParcel_UTILITY \"UTILITY\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_UTILITY,-1,-1;\
    RecentTaxParcel_APRLAND \"APRLAND\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_APRLAND,-1,-1;\
    RecentTaxParcel_APRBLDG \"APRBLDG\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_APRBLDG,-1,-1;\
    RecentTaxParcel_APRTOTAL \"APRTOTAL\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_APRTOTAL,-1,-1;\
    RecentTaxParcel_SALEDT \"SALEDT\" true true false 11 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_SALEDT,-1,-1;\
    RecentTaxParcel_PRICE \"PRICE\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_PRICE,-1,-1;\
    RecentTaxParcel_PREV_PRICE \"PREV_PRICE\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_PREV_PRICE,-1,-1;\
    RecentTaxParcel_SCHOOL_DIS \"SCHOOL_DIS\" true true false 5 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_SCHOOL_DIS,-1,-1;\
    RecentTaxParcel_COMM_STRUC \"COMM_STRUC\" true true false 3 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_COMM_STRUC,-1,-1;\
    RecentTaxParcel_COMM_YEAR_BUILT \"COMM_YEAR_BUILT\" true true false 4 Long 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_COMM_YEAR_BUILT,-1,-1;\
    RecentTaxParcel_COMM_BUILDING_SQ_FT \"COMM_BUILDING_SQ_FT\" true true false 4 Long 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_COMM_BUILDING_SQ_FT,-1,-1;\
    RecentTaxParcel_GRADE \"GRADE\" true true false 2 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_GRADE,-1,-1;\
    RecentTaxParcel_CDU \"CDU\" true true false 2 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_CDU,-1,-1;\
    RecentTaxParcel_DIST_NEW \"DIST_NEW\" true true false 3 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_DIST_NEW,-1,-1;\
    RecentTaxParcel_MUNICIPAL \"MUNICIPAL\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_MUNICIPAL,-1,-1;\
    RecentTaxParcel_SCHOOL \"SCHOOL\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_SCHOOL,-1,-1;\
    RecentTaxParcel_COUNTY \"COUNTY\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_COUNTY,-1,-1;\
    RecentTaxParcel_Muni_Tax_Total \"Muni_Tax_Total\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_Muni_Tax_Total,-1,-1;\
    RecentTaxParcel_School_Tax_Total \"School_Tax_Total\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_School_Tax_Total,-1,-1;\
    RecentTaxParcel_County_Tax_Total \"County_Tax_Total\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_County_Tax_Total,-1,-1;\
    RecentTaxParcel_Total_Tax \"Total_Tax\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_Total_Tax,-1,-1;\
    RecentTaxParcel_TAX1 \"TAX1\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_TAX1,-1,-1;\
    RecentTaxParcel_TAX2 \"TAX2\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_TAX2,-1,-1;\
    RecentTaxParcel_TAX3 \"TAX3\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_TAX3,-1,-1;\
    RecentTaxParcel_TAX4 \"TAX4\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_TAX4,-1,-1;\
    RecentTaxParcel_TAX5 \"TAX5\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_TAX5,-1,-1;\
    RecentTaxParcel_OTHER_TAX \"OTHER_TAX\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_OTHER_TAX,-1,-1;\
    RecentTaxParcel_ABTYPE \"ABTYPE\" true true false 254 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_ABTYPE,-1,-1;\
    RecentTaxParcel_FACE_TOTAL \"FACE_TOTAL\" true true false 50 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_FACE_TOTAL,-1,-1;\
    RecentTaxParcel_ABTYPE_1 \"ABTYPE_1\" true true false 254 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_ABTYPE_1,-1,-1;\
    RecentTaxParcel_FACE_TOTAL_1 \"FACE_TOTAL_1\" true true false 50 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_FACE_TOTAL_1,-1,-1;\
    RecentTaxParcel_HOMESTEAD \"HOMESTEAD\" true true false 3 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_HOMESTEAD,-1,-1;\
    RecentTaxParcel_FARMSTEAD \"FARMSTEAD\" true true false 3 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_FARMSTEAD,-1,-1;\
    RecentTaxParcel_PROGRAM \"PROGRAM\" true true false 255 Text 0 0 ,First,#,"+DataDriven_Convert+",RecentTaxParcel_PROGRAM,-1,-1;\
    OlderTaxParcel_OBJECTID \"OBJECTID\" true true false 4 Long 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_OBJECTID,-1,-1;\
    OlderTaxParcel_PIDN_LEASE \"PIDN_LEASE\" true true false 18 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_PIDN_LEASE,-1,-1;\
    OlderTaxParcel_PIDN_LEASE_1 \"PIDN_LEASE\" true true false 18 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_PIDN_LEASE_1,-1,-1;\
    OlderTaxParcel_PIDN \"PIDN\" true true false 13 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_PIDN,-1,-1;\
    OlderTaxParcel_DEED_BK \"DEED_BK\" true true false 8 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_DEED_BK,-1,-1;\
    OlderTaxParcel_DEED_PG \"DEED_PG\" true true false 8 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_DEED_PG,-1,-1;\
    OlderTaxParcel_PROPADR \"PROPADR\" true true false 54 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_PROPADR,-1,-1;\
    OlderTaxParcel_OWNER_FULL \"OWNER_FULL\" true true false 81 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_OWNER_FULL,-1,-1;\
    OlderTaxParcel_OWN_NAME1 \"OWN_NAME1\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_OWN_NAME1,-1,-1;\
    OlderTaxParcel_OWN_NAME2 \"OWN_NAME2\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_OWN_NAME2,-1,-1;\
    OlderTaxParcel_MAIL_ADDR_FULL \"MAIL_ADDR_FULL\" true true false 124 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_MAIL_ADDR_FULL,-1,-1;\
    OlderTaxParcel_MAIL_ADDR1 \"MAIL_ADDR1\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_MAIL_ADDR1,-1,-1;\
    OlderTaxParcel_MAIL_ADDR2 \"MAIL_ADDR2\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_MAIL_ADDR2,-1,-1;\
    OlderTaxParcel_MAIL_ADDR3 \"MAIL_ADDR3\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_MAIL_ADDR3,-1,-1;\
    OlderTaxParcel_PREV_OWNER \"PREV_OWNER\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_PREV_OWNER,-1,-1;\
    OlderTaxParcel_CLASS \"CLASS\" true true false 1 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_CLASS,-1,-1;\
    OlderTaxParcel_LUC \"LUC\" true true false 4 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_LUC,-1,-1;\
    OlderTaxParcel_ACRES \"ACRES\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_ACRES,-1,-1;\
    OlderTaxParcel_STYLE \"STYLE\" true true false 2 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_STYLE,-1,-1;\
    OlderTaxParcel_NUM_STORIE \"NUM_STORIE\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_NUM_STORIE,-1,-1;\
    OlderTaxParcel_RES_LIVING_AREA \"RES_LIVING_AREA\" true true false 4 Long 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_RES_LIVING_AREA,-1,-1;\
    OlderTaxParcel_YRBLT \"YRBLT\" true true false 2 Short 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_YRBLT,-1,-1;\
    OlderTaxParcel_CLEAN_GREEN \"CLEAN_GREEN\" true true false 3 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_CLEAN_GREEN,-1,-1;\
    OlderTaxParcel_HEATSYS \"HEATSYS\" true true false 2 Short 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_HEATSYS,-1,-1;\
    OlderTaxParcel_FUEL \"FUEL\" true true false 2 Short 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_FUEL,-1,-1;\
    OlderTaxParcel_UTILITY \"UTILITY\" true true false 40 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_UTILITY,-1,-1;\
    OlderTaxParcel_APRLAND \"APRLAND\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_APRLAND,-1,-1;\
    OlderTaxParcel_APRBLDG \"APRBLDG\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_APRBLDG,-1,-1;\
    OlderTaxParcel_APRTOTAL \"APRTOTAL\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_APRTOTAL,-1,-1;\
    OlderTaxParcel_SALEDT \"SALEDT\" true true false 11 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_SALEDT,-1,-1;\
    OlderTaxParcel_PRICE \"PRICE\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_PRICE,-1,-1;\
    OlderTaxParcel_PREV_PRICE \"PREV_PRICE\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_PREV_PRICE,-1,-1;\
    OlderTaxParcel_SCHOOL_DIS \"SCHOOL_DIS\" true true false 5 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_SCHOOL_DIS,-1,-1;\
    OlderTaxParcel_COMM_STRUC \"COMM_STRUC\" true true false 3 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_COMM_STRUC,-1,-1;\
    OlderTaxParcel_COMM_YEAR_BUILT \"COMM_YEAR_BUILT\" true true false 4 Long 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_COMM_YEAR_BUILT,-1,-1;\
    OlderTaxParcel_COMM_BUILDING_SQ_FT \"COMM_BUILDING_SQ_FT\" true true false 4 Long 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_COMM_BUILDING_SQ_FT,-1,-1;\
    OlderTaxParcel_GRADE \"GRADE\" true true false 2 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_GRADE,-1,-1;\
    OlderTaxParcel_CDU \"CDU\" true true false 2 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_CDU,-1,-1;\
    OlderTaxParcel_DIST_NEW \"DIST_NEW\" true true false 3 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_DIST_NEW,-1,-1;\
    OlderTaxParcel_MUNICIPAL \"MUNICIPAL\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_MUNICIPAL,-1,-1;\
    OlderTaxParcel_SCHOOL \"SCHOOL\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_SCHOOL,-1,-1;\
    OlderTaxParcel_COUNTY \"COUNTY\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_COUNTY,-1,-1;\
    OlderTaxParcel_Muni_Tax_Total \"Muni_Tax_Total\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_Muni_Tax_Total,-1,-1;\
    OlderTaxParcel_School_Tax_Total \"School_Tax_Total\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_School_Tax_Total,-1,-1;\
    OlderTaxParcel_County_Tax_Total \"County_Tax_Total\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_County_Tax_Total,-1,-1;\
    OlderTaxParcel_Total_Tax \"Total_Tax\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_Total_Tax,-1,-1;\
    OlderTaxParcel_TAX1 \"TAX1\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_TAX1,-1,-1;\
    OlderTaxParcel_TAX2 \"TAX2\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_TAX2,-1,-1;\
    OlderTaxParcel_TAX3 \"TAX3\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_TAX3,-1,-1;\
    OlderTaxParcel_TAX4 \"TAX4\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_TAX4,-1,-1;\
    OlderTaxParcel_TAX5 \"TAX5\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_TAX5,-1,-1;\
    OlderTaxParcel_OTHER_TAX \"OTHER_TAX\" true true false 8 Double 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_OTHER_TAX,-1,-1;\
    OlderTaxParcel_ABTYPE \"ABTYPE\" true true false 254 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_ABTYPE,-1,-1;\
    OlderTaxParcel_FACE_TOTAL \"FACE_TOTAL\" true true false 50 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_FACE_TOTAL,-1,-1;\
    OlderTaxParcel_ABTYPE_1 \"ABTYPE_1\" true true false 254 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_ABTYPE_1,-1,-1;\
    OlderTaxParcel_FACE_TOTAL_1 \"FACE_TOTAL_1\" true true false 50 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_FACE_TOTAL_1,-1,-1;\
    OlderTaxParcel_HOMESTEAD \"HOMESTEAD\" true true false 3 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_HOMESTEAD,-1,-1;\
    OlderTaxParcel_FARMSTEAD \"FARMSTEAD\" true true false 3 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_FARMSTEAD,-1,-1;\
    OlderTaxParcel_PROGRAM \"PROGRAM\" true true false 255 Text 0 0 ,First,#,"+DataDriven_Convert+",OlderTaxParcel_PROGRAM,-1,-1;\
    Type \"Type\" true true false 255 Text 0 0 ,First,#,"+DataDriven_Convert+",Type,-1,-1;\
    Shape_Length \"Shape_Length\" false true true 8 Double 0 0 ,First,#,"+DataDriven_Convert+",Shape_Length,-1,-1;\
    Shape_Area \"Shape_Area\" false true true 8 Double 0 0 ,First,#,"+DataDriven_Convert+",Shape_Area,-1,-1""", config_keyword="")

#######################################################################   Data Driven Pages Section   ######################################################################################################################################################################################

    #import system

    def pause():
        programPause = raw_input("Type ENTER to continue")

    #message (report, "Make sure MXDs are set up properly for data driven pages. Type Enter to Continue\n")
    #pause()

    # This section will start the Data Driven Pages section. Based on Count Totals, PDFs will be created differently depending
    # If Total Count is not 0 then proceed. Else move on
    if (AllTotalCount != 0):
        message (report, "Starting Data Driven Pages\n")

        # set variables
        # List used to feed Data Driven Pages. Populated in Search Cursor section
        PDFList = []
        # Variable used in SearchCursor
        PDFBuild = os.path.join(DataDriven_Workplace,"UpdatedParcels_DataDriven")

        # populate buildList with building numbers
        message (report, "Appending PIDN LEASE Numbers to PDF LIST\n")
        with arcpy.da.SearchCursor(PDFBuild, ["RecentTaxParcel_PIDN_LEASE"]) as cursor:
            for row in cursor:
                PDFList.append(row[0])

        # Output Directory where updated PDFs will be housed
        outDir = r"\\YCPCFS\GIS_Projects\IS\Projects\TaxParcel_DataDrivenPage\PDF"

        # if Total Count is not 0 and then less then 3000 then continue
        if (AllTotalCount <= 3000):
                message (report, "Under 3000 parcels to update. Use under 3000 parcel criteria\n")
                message (report, "Deleting Old PDFs from Directory {}\n".format(outDir))
                # for loop deletes any extisting PDFs in Output Directory
                for the_file in os.listdir(outDir):
                    file_path = os.path.join(outDir, the_file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        #elif os.path.isdir(file_path): shutil.rmtree(file_path)
                    except Exception as e:
                        print(e)

                # Variable to show where map document is used for Data Driven Pages
                mxd = arcpy.mapping.MapDocument(r"\\YCPCFS\GIS_Projects\IS\Projects\TaxParcel_DataDrivenPage\TaxParcel_11x17B_Update.mxd")

                # Data Driven Variable
                ddp = mxd.dataDrivenPages

                # Refresh DDP
                message (report, "Refreshing MXD {}\n".format(mxd))
                mxd.dataDrivenPages.refresh()

                # message (report, "Saving mxd {}\n".format(mxd))
                # Saves and time stamps mxd which will timestamp Exported PDFs
                message (report, "Saving MXD {}\n".format(mxd))
                mxd.save()

                # Variable used to determine what data driven page is currently being printed. This will be populated in the "for" loop
                PDFCount = 0

                # Section that loops thru values in PDFDList. Values are Properities from Update_DataDriven Layer
                for pageName in PDFList:
                		pageID = mxd.dataDrivenPages.getPageIDFromName(pageName)
                		mxd.dataDrivenPages.currentPageID = pageID
                		pageNameClean = pageName.replace("/","_")
                                PDFCount = PDFCount + 1

                		try:
                			arcpy.mapping.ExportToPDF(mxd, os.path.join(outDir, "TaxParcel_" + pageNameClean + ".pdf"), resolution=300, image_quality = "BETTER")
                                        #message (report, "Printing {} of {} Data Driven Pages".format(len(PDFList,len(PDFList)))
                                        message (report, "Printing {} of {}: Exporting PIDN LEASE NUMBER: {}".format(PDFCount,len(PDFList),pageNameClean))
                		except Exception, e:
                			tb = sys.exc_info()[2]
                			message (report, "Failed at Line %i \n" % tb.tb_lineno)
                			message (report, "Error: {} \n".format(e.message))

# Old Data Driven Pages Step. Keeping just in case
##                 # For Loop: Continues to loop thru the rest of the data driven pages until done
##                for i in range(1, mxd.dataDrivenPages.pageCount + 1):
##                    ddp.currentPageID = i
##                    row = ddp.pageRow
##                    pgName = row.getValue(ddp.pageNameField.name)
##                    print "Exporting {0}: page {1} of {2}".format(pgName,(mxd.dataDrivenPages.currentPageID), str(mxd.dataDrivenPages.pageCount))
##                    message (report, "Exporting {0}: page {1} of {2}".format(pgName,(mxd.dataDrivenPages.currentPageID), str(mxd.dataDrivenPages.pageCount)))
##                    arcpy.mapping.ExportToPDF(mxd, os.path.join(outDir, "TaxParcel_" + pgName + ".pdf"), resolution = 150, image_quality = "BETTER")
##
                message (report, "Exported {0} pages of {1}\n".format((PDFCount),str(mxd.dataDrivenPages.pageCount)))

                # deletes any locks on mxd
                del mxd

        # if Total Count is not 0 and then less then 3000 then continue
        if (AllTotalCount > 3000):
                message (report, "Over 3000 parcels to update. Use over 3000 parcel criteria\n")
                message (report, "Deleting Old PDFs from Directory {}\n".format(outDir))
                # for loop deletes any extisting PDFs in Output Directory
                for the_file in os.listdir(outDir):
                    file_path = os.path.join(outDir, the_file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        #elif os.path.isdir(file_path): shutil.rmtree(file_path)
                    except Exception as e:
                        print(e)

                # Variable to show where map document is used for Data Driven Pages
                mxd = arcpy.mapping.MapDocument(r"\\YCPCFS\GIS_Projects\IS\Projects\TaxParcel_DataDrivenPage\TaxParcel_11x17B_Update.mxd")

                # Data Driven Variable
                ddp = mxd.dataDrivenPages

                # Refresh DDP
                message (report, "Refreshing MXD {}\n".format(mxd))
                mxd.dataDrivenPages.refresh()

                # message (report, "Saving mxd {}\n".format(mxd))
                # Saves and time stamps mxd which will timestamp Exported PDFs
                message (report, "Saving MXD {}\n".format(mxd))
                mxd.save()

                # Variable used to determine what data driven page is currently being printed. This will be populated in the "for" loop
                PDFCount = 0

                # Section that loops thru values in PDFDList. Values are Properities from Update_DataDriven Layer
                for pageName in PDFList[0:3000]:
                		pageID = mxd.dataDrivenPages.getPageIDFromName(pageName)
                		mxd.dataDrivenPages.currentPageID = pageID
                		pageNameClean = pageName.replace("/","_")
                                PDFCount = PDFCount + 1

                		try:
                			arcpy.mapping.ExportToPDF(mxd, os.path.join(outDir, "TaxParcel_" + pageNameClean + ".pdf"), resolution=300, image_quality = "BETTER")
                                        #message (report, "Printing {} of {} Data Driven Pages".format(len(PDFList,len(PDFList)))
                                        message (report, "Printing {} of {}: Exporting PIDN LEASE NUMBER: {}".format(PDFCount,len(PDFList),pageNameClean))
                		except Exception, e:
                			tb = sys.exc_info()[2]
                			message (report, "Failed at Line %i \n" % tb.tb_lineno)
                			message (report, "Error: {} \n".format(e.message))

# Old Data Driven Pages Step. Keeping just in case
##                # For Loop: Loops through first 3000 Data Driven Pages
##                message (report, "Starting First Loop of Data Driven Pages")
##                for i in range(1, 3000):
##                    ddp.currentPageID = i
##                    row = ddp.pageRow
##                    pgName = row.getValue(ddp.pageNameField.name)
##                    print "Exporting {0}: page {1} of {2}".format(pgName,(mxd.dataDrivenPages.currentPageID), str(mxd.dataDrivenPages.pageCount))
##                    message (report, "Exporting {0}: page {1} of {2}".format(pgName,(mxd.dataDrivenPages.currentPageID), str(mxd.dataDrivenPages.pageCount)))
##                    arcpy.mapping.ExportToPDF(mxd, os.path.join(outDir, "TaxParcel_" + pgName + ".pdf"), resolution = 150, image_quality = "BETTER")

                # deletes any locks on mxd
                del mxd

                # Variable to show where map document is used for Data Driven Pages
                mxd = arcpy.mapping.MapDocument(r"\\YCPCFS\GIS_Projects\IS\Projects\TaxParcel_DataDrivenPage\TaxParcel_11x17B_Update2.mxd")

                # Data Driven Variable
                ddp = mxd.dataDrivenPages

                # Refresh DDP
                message (report, "\nRefreshing MXD {}\n".format(mxd))
                mxd.dataDrivenPages.refresh()

                # message (report, "Saving mxd {}\n".format(mxd))
                # Saves and time stamps mxd which will timestamp Exported PDFs
                message (report, "Saving MXD {}\n".format(mxd))
                mxd.save()

                # Section that loops thru values in PDFDList. Values are Properities from Update_DataDriven Layer
                for pageName in PDFList[3000:mxd.dataDrivenPages.pageCount + 1]:
                		pageID = mxd.dataDrivenPages.getPageIDFromName(pageName)
                		mxd.dataDrivenPages.currentPageID = pageID
                		pageNameClean = pageName.replace("/","_")
                                PDFCount = PDFCount + 1

                		try:
                			arcpy.mapping.ExportToPDF(mxd, os.path.join(outDir, "TaxParcel_" + pageNameClean + ".pdf"), resolution=300, image_quality = "BETTER")
                                        #message (report, "Printing {} of {} Data Driven Pages".format(len(PDFList,len(PDFList)))
                                        message (report, "Printing {} of {}: Exporting PIDN LEASE NUMBER: {}".format(PDFCount,len(PDFList),pageNameClean))
                		except Exception, e:
                			tb = sys.exc_info()[2]
                			message (report, "Failed at Line %i \n" % tb.tb_lineno)
                			message (report, "Error: {} \n".format(e.message))

# Old Data Driven Pages Step. Keeping just in case
##                 # For Loop: Continues to loop thru the rest of the data driven pages until done
##                message (report, "Starting Second Loop of Data Driven Pages")
##                for i in range(3000, mxd.dataDrivenPages.pageCount + 1):
##                    ddp.currentPageID = i
##                    row = ddp.pageRow
##                    pgName = row.getValue(ddp.pageNameField.name)
##                    print "Exporting {0}: page {1} of {2}".format(pgName,(mxd.dataDrivenPages.currentPageID), str(mxd.dataDrivenPages.pageCount))
##                    message (report, "Exporting {0}: page {1} of {2}".format(pgName,(mxd.dataDrivenPages.currentPageID), str(mxd.dataDrivenPages.pageCount)))
##                    arcpy.mapping.ExportToPDF(mxd, os.path.join(outDir, "TaxParcel_" + pgName + ".pdf"), resolution = 150, image_quality = "BETTER")

                message (report, "Exported {0} pages of {1}\n".format((PDFCount),str(mxd.dataDrivenPages.pageCount)))

                #Deletes any locks on mxd
                del mxd

    # If Total Count is 0 then proceed.
    else:
        message (report, "No Data Driven Pages Updates needed. Total Number of Updates = 0\n")

# Section for error messaging
except EnvironmentError as e:
    ErrorMessageEnvironment(e)
except Exception as e:
    ErrorMessageException(e)

finally:
    try:
        message (report, "TaxParcel_DataDrivenPages_Update.py script is Completed\n")
        # Script Completion DateTime for Elapsed Time Calculation
        ScriptEndTime = datetime.datetime.now()
        # Total Script Elapsed Time Calculation
        ScriptElapsedTime = ScriptEndTime - ScriptStartTime
        # Prints out Total Time of Script
        message (report, "Total Elapsed Time:  - " + str(ScriptElapsedTime) + "\n")
        # del mxd
        message (report, "Done!")
        report.close()
    except:
        pass

#Script Ended

