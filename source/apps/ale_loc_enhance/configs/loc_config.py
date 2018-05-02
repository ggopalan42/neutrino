obj_id_params:        # These are the parameters for object identification
    confidence: 0.2   # The confidence level above which objects are identified

kafka:
    kafka_broker_hostname: '10.2.13.29'
    kafka_broker_port: '9092'

ale_params:     # These are the parameters for the Aruba ALE
    # ale_rem is used while accessing REST or zeromq via remote host
    ale_rem_hostname: 10.1.3.30
    ale_rem_port: 7779
   
cams_config:         # Config of camera information
    cams_config_fn:
        - aruba_cams.yml  

# Aruba Campus info
# This information was gotten from ALE via the REST interface. Mostly
# by doing curl commands. Example below:
#    curl -u admin --insecure https://10.1.3.30/api/v1/access_point
# This can easily be automated in future

ale_campus_info:
    - SLR:
        description: "Aruba's Santa Clara HQ Campus"
        campus_id: A6E8081396B33633ABA6946E6D33339A
        campus_name: SLR
        building:
            - SLR01:
                  building_id: 418F3C0516FC3EE49EE01A20E00835DE
                  building_name: SLR01
                  floor:
                      - floor1:
                          floor_id: 99E9DB7AAEA13F07B783CB4650811630
                          floor_name: "Floor 1"
                          floor_image: slr01_floor1_99E9DB7AAEA13F07B783CB4650811630.jpg
                          floor_dwg_width: 318
                          floor_dwg_length: 198
                          floor_dwg_unit: feet
                      - floor2:
                          floor_id: 429191A0DF4D392C8DF9ED35A2CE444D
                          floor_name: "Floor 2"
                          floor_image: slr01_floor2_429191A0DF4D392C8DF9ED35A2CE444D.jpg
                          floor_dwg_width: 320
                          floor_dwg_length: 204
                          floor_dwg_unit: feet
                      - floor3:
                          floor_id: 044EBA35ADB937D9B20F040E1C1CC5CB
                          floor_name: "Floor 3"
                          floor_image: slr01_floor3_044EBA35ADB937D9B20F040E1C1CC5CB.jpg
                          floor_dwg_width: 303
                          floor_dwg_length: 194
                          floor_dwg_unit: feet
                      - floor5:
                          floor_id: 46C2266F22DE364BBE966B37ED54E5FF
                          floor_name: "Floor 5"
                          floor_image: slr01_floor5_46C2266F22DE364BBE966B37ED54E5FF.jpg
                          floor_dwg_width: 306
                          floor_dwg_length: 195
                          floor_dwg_unit: feet
            - SLR01-4:
                  building_id: 5F971B484A0539579569BA33AB90A5CA
                  building_name: SLR01-4
                  floor:
                      - floor4:
                          floor_id: 2CE68FBE28A4335B9C7819B227C701B9
                          floor_name: "Floor 4"
                          floor_image: slr01-4_floor4_2CE68FBE28A4335B9C7819B227C701B9.jpg
                          floor_dwg_width: 303
                          floor_dwg_length: 194
                          floor_dwg_unit: feet
            - SLR02:
                  building_id: B92C620812A638FC9741BF39129B05A2
                  building_name: SLR02
                  floor:
                      - floor1:
                          floor_id: C56F383AAF5E3B61A428D9467E0231D3
                          floor_name: "Floor 1"
                          floor_image: slr02_floor1_C56F383AAF5E3B61A428D9467E0231D3.jpg
                          floor_dwg_width: 324
                          floor_dwg_length: 137
                          floor_dwg_unit: feet

    - Portland:
        description: "Aruba's Portland Campus"
        campus_id: 416D1F0790B0349DA626DF97944F9AC5
        campus_name: "Portland, OR"
        building:
            - BLOCK_300:
                  building_id: E6E596E653DD3181BFE50342225F8A0F
                  building_name: "BLOCK 300"
                  floor:
                      - floor7:
                          floor_id: 26048610BAE2353A9581332C5C5790A0
                          floor_name: "Floor 7"
                          floor_image: PORblock300_floor1_26048610BAE2353A9581332C5C5790A0.jpg
                          floor_dwg_width: 214
                          floor_dwg_length: 218
                          floor_dwg_unit: feet
