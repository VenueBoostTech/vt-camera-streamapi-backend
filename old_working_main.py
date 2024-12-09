from fastapi import FastAPI, HTTPException, Depends,Query,Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime,Text,insert,text,Boolean
import uuid
from pydantic import BaseModel  # Ensure this import is included
from datetime import datetime
import pandas as pd
from typing import Optional
import logging
import base64
import os
from datetime import datetime
from uuid import uuid4
from typing import List  # Import List for type hinting
import json  # Import json to handle JSON data

app = FastAPI()
logger = logging.getLogger(__name__)
# Create the FastAPI app
app = FastAPI()

# Create an asynchronous engine and session
DATABASE_URL = "sqlite+aiosqlite:///./building_traffic.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency for getting the database session
async def get_db():
    async with async_session() as session:
        yield session

class Configuration(Base):
    __tablename__ = "Configuration"
    
    id = Column(Integer, primary_key=True, index=True)
    x1_point = Column(Integer, nullable=False)
    y1_point = Column(Integer, nullable=False)
    x2_point = Column(Integer, nullable=False)
    y2_point = Column(Integer, nullable=False)

# Define your models here (make sure these are defined correctly)
class EntryLog(Base):
    __tablename__ = 'EntryLog'
    id = Column(Integer, primary_key=True, index=True)
    cameraId = Column(Text, index=True, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    personId = Column(Text, nullable=False, index=True)
    gender = Column(Text, nullable=False, index=True)
    age = Column(Text, nullable=False, index=True)

class CameraMetadata(Base):
    __tablename__ = 'CameraMetadata'
    id = Column(Integer, primary_key=True, index=True)
    cameraId = Column(Text, unique=True, nullable=False)
    location = Column(Text, nullable=False)
    resolution = Column(Text, nullable=False)

class ExitLog(Base):
    __tablename__ = 'ExitLog'
    id = Column(Integer, primary_key=True, index=True)
    cameraId = Column(Text, index=True, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    personId = Column(Text, nullable=False, index=True)

class TrackingLog(Base):
    __tablename__ = 'TrackingLog'
    id = Column(Integer, primary_key=True, index=True)
    cameraId = Column(Text, index=True, nullable=False)
    personId = Column(Text, index=True, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    bbox = Column(Text, nullable=False)
    centroid = Column(Text, nullable=False)

# Stream model
class Camera(Base):
    __tablename__ = 'Camera'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cameraId = Column(Text, nullable=False)
    cameraUrl = Column(Text, nullable=False)
    cameraStatus = Column(Boolean, default=True)
    cameraConfig = Column(Text)  # This will store JSON data as a string

# Pydantic model for request validation
class CameraCreate(BaseModel):
    cameraId: str
    cameraUrl: str
    cameraStatus: bool
    cameraConfig: dict


# Define Pydantic models for request validation
class EntryLogCreate(BaseModel):
    cameraId: str
    timestamp: datetime
    personId: str
    gender: str
    age: str

class ExitLogCreate(BaseModel):
    cameraId: str
    timestamp: datetime
    personId: str

# Define a Pydantic model for the request body
class ConfigurationRequest(BaseModel):
    x1_point: int
    y1_point: int
    x2_point: int
    y2_point: int

# Mount the static directory
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.post("/api/configuration")
async def create_or_update_configuration(config: ConfigurationRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Fetch the existing Configuration entry
        result = await db.execute(select(Configuration).filter_by(id=1))
        existing_config = result.scalars().first()
        
        if existing_config:
            # Update the existing entry
            existing_config.x1_point = config.x1_point
            existing_config.y1_point = config.y1_point
            existing_config.x2_point = config.x2_point
            existing_config.y2_point = config.y2_point
        else:
            # Create a new entry
            new_config = Configuration(
                id=1, 
                x1_point=config.x1_point, 
                y1_point=config.y1_point, 
                x2_point=config.x2_point, 
                y2_point=config.y2_point
            )
            db.add(new_config)
        
        await db.commit()
        return {
            "message": "Configuration entry updated successfully",
            "x1_point": config.x1_point,
            "y1_point": config.y1_point,
            "x2_point": config.x2_point,
            "y2_point": config.y2_point
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")
    finally:
        await db.close()


@app.get("/api/configuration")
async def get_configuration(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Configuration).filter_by(id=1))
        config = result.scalars().first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Configuration entry not found")
        
        return {
            "id": config.id,
            "x1_point": config.x1_point,
            "y1_point": config.y1_point,
            "x2_point": config.x2_point,
            "y2_point": config.y2_point
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration: {str(e)}")
    finally:
        await db.close()


# POST endpoint to insert an entry log
@app.post("/entrylog/")
async def create_entry_log(entry_log: EntryLogCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Prepare the insert statement
        stmt = insert(EntryLog).values(
            cameraId=entry_log.cameraId,
            timestamp=entry_log.timestamp,
            personId=entry_log.personId,
            gender=entry_log.gender,
            age=entry_log.age
        )
        
        # Execute the insert statement
        await db.execute(stmt)
        
        # Commit the transaction
        await db.commit()
        
        return {"message": "Entry log created successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create entry log: {str(e)}")
    finally:
        await db.close()

# POST endpoint to insert an exit log
@app.post("/exitlog/")
async def create_exit_log(exit_log: ExitLogCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Prepare the insert statement
        stmt = insert(ExitLog).values(
            cameraId=exit_log.cameraId,
            timestamp=exit_log.timestamp,
            personId=exit_log.personId
        )
        
        # Execute the insert statement
        await db.execute(stmt)
        
        # Commit the transaction
        await db.commit()
        
        return {"message": "Exit log created successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create exit log: {str(e)}")
    finally:
        await db.close()




# Modify the POST endpoint to add or update a camera entry
@app.post("/api/camera")
async def create_or_update_camera(camera: CameraCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Generate a unique cameraId using uuid
        cameraId = str(uuid4())
        
        # Check if a camera with the same URL already exists
        result = await db.execute(select(Camera).filter_by(cameraUrl=camera.cameraUrl))
        existing_camera = result.scalars().first()
        
        if existing_camera:
            # Update the existing camera entry
            existing_camera.cameraStatus = camera.cameraStatus
            existing_camera.cameraConfig = json.dumps(camera.cameraConfig)
        else:
            # Create a new camera entry
            new_camera = Camera(
                cameraId=cameraId,
                cameraUrl=camera.cameraUrl,
                cameraStatus=camera.cameraStatus,
                cameraConfig=json.dumps(camera.cameraConfig)
            )
            db.add(new_camera)
        
        await db.commit()
        return {
            "message": "Camera entry added or updated successfully",
            "cameraId": cameraId,
            "cameraUrl": camera.cameraUrl
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update Camera: {str(e)}")
    finally:
        await db.close()

# Modify the GET endpoint to retrieve a camera entry by URL
@app.get("/api/camera", response_model=List[dict])
async def get_all_cameras(db: AsyncSession = Depends(get_db)):
    logger.info("Received request to /api/cameras endpoint")
    try:
        # Fetch all camera entries
        result = await db.execute(select(Camera))
        cameras = result.scalars().all()
        
        if not cameras:
            logger.warning("No camera entries found")
            raise HTTPException(status_code=404, detail="No camera entries found")
        
        # Convert camera entries to a list of dictionaries
        camera_list = []
        for camera in cameras:
            # Handle potential None value for cameraConfig
            try:
                # Use '{}' as a default if camera.cameraConfig is None
                camera_config = json.loads(camera.cameraConfig) if camera.cameraConfig else {}
            except (TypeError, json.JSONDecodeError) as e:
                logger.error(f"Failed to parse cameraConfig for camera ID {camera.id}: {e}")
                camera_config = {}  # Fallback to an empty dict or another default value
            
            camera_list.append({
                "id": camera.id,
                "cameraId": camera.cameraId,
                "cameraUrl": camera.cameraUrl,
                "cameraStatus": camera.cameraStatus,
                "cameraConfig": camera_config,
            })

        logger.info(f"Successfully retrieved {len(camera_list)} camera entries")
        return camera_list

    except Exception as e:
        logger.error(f"Error retrieving cameras: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cameras: {str(e)}")

    finally:
        await db.close()
        logger.info("Database session closed")


@app.get('/api/people-count')
async def people_count(start_time: str, end_time: str, camera_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")
        print("Start Time:", start_time)
        print("End Time:", end_time)
        camera_id = camera_id.strip()
        query = select(EntryLog).filter(EntryLog.timestamp >= start_time, EntryLog.timestamp <= end_time)
        
        if camera_id:
            query = query.filter(EntryLog.cameraId == camera_id)
        
        result = await db.execute(query)
        entries = result.scalars().all()
        
        entry_count = len(entries)
        
        # For exit_count, you should do something similar
        query = select(ExitLog).filter(ExitLog.timestamp >= start_time, ExitLog.timestamp <= end_time)
        if camera_id:
            query = query.filter(ExitLog.cameraId == camera_id)
        
        result = await db.execute(query)
        exits = result.scalars().all()
        
        exit_count = len(exits)
        
        return {
            "camera_id": camera_id,
            "total_entry_count": entry_count,
            "total_exit_count": exit_count,
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch counts: {str(e)}")

@app.get('/api/demographics')
async def demographics(
    start_time: str, 
    end_time: str, 
    camera_id: Optional[str] = None, 
    db: AsyncSession = Depends(get_db)
):
    try:
        # Parse timestamps
        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")
        logger.info(f"Start Time: {start_time}")
        logger.info(f"End Time: {end_time}")

        if camera_id:
            camera_id = camera_id.strip()

        # Build query
        query = select(EntryLog).filter(
            EntryLog.timestamp >= start_time,
            EntryLog.timestamp <= end_time
        )
        
        if camera_id:
            query = query.filter(EntryLog.cameraId == camera_id)

        # Execute query and fetch results
        result = await db.execute(query)
        entries = result.scalars().all()  # Use scalars().all() to get list of EntryLog objects

        # Print entries for debugging
        for entry in entries:
            logger.info(f"Entry: {entry}")
            print(f"{entry.gender}")

        # Check entries
        if not entries:
            logger.info("No entries found")

        total_male = sum(1 for entry in entries if entry.gender == 'M')
        total_female = sum(1 for entry in entries if entry.gender == 'F')
        print(f"Total Male:{total_male}")
        print(f"Total Female:{total_female}")
        age_groups = {
            "0-15": sum(1 for entry in entries if entry.age == '0-15'),
            "15-30": sum(1 for entry in entries if entry.age == '15-30'),
            "30-45": sum(1 for entry in entries if entry.age == '30-45'),
            "45-60": sum(1 for entry in entries if entry.age == '45-60'),
            "60+": sum(1 for entry in entries if entry.age == '60+')
        }

        return {
            "camera_id": camera_id,
            "demographics": {
                "male": total_male,
                "female": total_female,
                "age_groups": age_groups
            }
        }
    except Exception as e:
        logger.error(f"Detailed Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch demographic data")   
    
@app.get('/api/traffic-trends')
async def traffic_trends(interval: str, start_time: str, end_time: str, camera_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        print("--------------------Request Data Received --------------------------")
        print(start_time)
        print(end_time)
        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")
        print(start_time)
        print(end_time)
        
        query = select(EntryLog.timestamp).filter(EntryLog.timestamp >= start_time, EntryLog.timestamp <= end_time)
        if camera_id:
            query = query.filter(EntryLog.cameraId == camera_id)
        
        result = await db.execute(query)
        timestamps = result.scalars().all()
        
        df = pd.DataFrame(timestamps, columns=['timestamp'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Resampling according to the interval
        df.set_index('timestamp', inplace=True)
        if interval == 'hourly':
            result = df.resample('H').size().reset_index(name='count')
        elif interval == 'daily':
            result = df.resample('D').size().reset_index(name='count')
        elif interval == 'weekly':
            result = df.resample('W').size().reset_index(name='count')

        result['date'] = result['timestamp'].dt.strftime('%Y-%m-%d')

        if interval == 'hourly':
            hour = result['timestamp'].dt.strftime('%H')
            next_hour = result['timestamp'] + pd.DateOffset(hours=1)
            result['hour'] = hour + '-' + next_hour.dt.strftime('%H')

        result.drop('timestamp', axis=1, inplace=True)

        return {
            "camera_id": camera_id,
            "traffic_trends": [
                {
                    "interval": interval.capitalize(),
                    "data": result.to_dict(orient='records')
                }
            ]
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch traffic trends: {str(e)}")


@app.get('/api/demographic-traffic-overview')
async def demographic_traffic_overview(
    interval: str = Query(..., regex="^(hourly|daily|weekly)$"),
    start_time: str = Query(..., regex="^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"),
    end_time: str = Query(..., regex="^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"),
    camera_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Set pandas options to display all data
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_colwidth', None)
        pd.set_option('display.width', None)

        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")

        query = select(EntryLog).filter(EntryLog.timestamp >= start_time, EntryLog.timestamp <= end_time)
        if camera_id:
            query = query.filter(EntryLog.cameraId == camera_id)

        result = await db.execute(query)
        data = result.scalars().all()

        if data:
            print(f"First entry: {data[0]}")
            print(f"Total entries fetched: {len(data)}")

        df = pd.DataFrame(
            [(entry.id, entry.cameraId, entry.timestamp, entry.personId, entry.age, entry.gender) for entry in data],
            columns=['id', 'cameraId', 'timestamp', 'personId', 'age', 'gender']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        if interval == 'hourly':
            grouped = df.resample('H')
        elif interval == 'daily':
            grouped = df.resample('D')
        elif interval == 'weekly':
            grouped = df.resample('W')

        # Print the full grouped data for gender and age
        # print("---------------------------Grouped gender---------------------------------")
        # print(grouped['gender'].apply(list))
        # print("---------------------------Grouped age---------------------------------")
        # print(grouped['age'].apply(list))

        result = grouped['id'].count().rename('total_count').to_frame()
        gender_counts = grouped['gender'].apply(lambda x: x.value_counts().to_dict())
        age_counts = grouped['age'].apply(lambda x: x.value_counts().to_dict())
        # print("----------------------Processing after grouping--------------------------")

        intervals_data = []
        for i, (interval_start, row) in enumerate(result.iterrows()):
            try:
                # print(f"Processing interval {i + 1}: {interval_start}")

                genders = gender_counts.get(interval_start, {})
                # print(f"Gender counts for interval {i + 1}: {genders}")

                ages = age_counts.get(interval_start, {})
                # print(f"Age counts for interval {i + 1}: {ages}")

                if interval == 'hourly':
                    interval_end = interval_start + pd.DateOffset(hours=1)
                elif interval == 'daily':
                    interval_end = interval_start + pd.DateOffset(days=1)
                else:  # interval == 'weekly'
                    interval_end = interval_start + pd.DateOffset(weeks=1)
                
                interval_string = f"{interval_start.strftime('%Y-%m-%d %H:%M:%S')} - {interval_end.strftime('%Y-%m-%d %H:%M:%S')}"
                # print(f"Interval string for interval {i + 1}: {interval_string}")

                interval_data = {
                    "interval": interval_string,
                    "total_count": int(row['total_count']),
                    "demographics": {
                        "male": int(genders.get('M', 0)),
                        "female": int(genders.get('F', 0)),
                        "age_groups": {
                            "0-15": int(ages.get('0-15', 0)),
                            "15-30": int(ages.get('15-30', 0)),
                            "30-45": int(ages.get('30-45', 0)),
                            "45-60": int(ages.get('45-60', 0)),
                            "60+": int(ages.get('60+', 0))
                        }
                    }
                }
                # print(f"Generated interval data for interval {i + 1}: {interval_data}")
                intervals_data.append(interval_data)

            except Exception as e:
                # print(f"Error occurred in interval {i + 1}: {interval_start}")
                print(f"Exception: {e}")
                # raise

        return {
            "camera_id": camera_id,
            "intervals_data": intervals_data
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch demographic and traffic overview: {str(e)}")


@app.post("/api/heatmap")
async def receive_heatmap_image(request: Request):
    try:
        # Parse the incoming JSON request body
        data = await request.json()
        
        # Extract the base64 string and cameraId from the JSON payload
        base64_image = data.get("heatmap")
        camera_id = data.get("cameraId")
        
        if not base64_image:
            return {"status": "error", "message": "No image data provided", "code": 400}
        
        if not camera_id:
            return {"status": "error", "message": "No camera ID provided", "code": 400}
        
        # Decode the base64 string
        image_data = base64.b64decode(base64_image)
        
        # Define the directory path based on the cameraId
        directory_path = os.path.join("images", camera_id)
        
        # Create the directory if it does not exist
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        
        # Generate a unique filename with a timestamp and UUID
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4()}.jpg"  # You can switch to .png if needed
        
        # Define the file path
        file_path = os.path.join(directory_path, filename)
        
        # Save the image to the specified path
        with open(file_path, "wb") as file:
            file.write(image_data)
        
        return {"status": "success", "filename": filename, "cameraId": camera_id}
    
    except Exception as e:
        return {"status": "error", "message": f"An error occurred: {str(e)}", "code": 500}


@app.get('/api/heatmap')
async def heatmap(cameraId: str = Query(...)):
    try:
        # Define the directory path based on the cameraId
        directory_path = os.path.join("images", cameraId)

        # Check if the directory exists
        if not os.path.exists(directory_path):
            return {"status": "error", "message": f"No folder found for cameraId: {cameraId}", "code": 404}

        # Get the list of all image files in the directory
        image_files = os.listdir(directory_path)

        # Base URL for images (assumes API URL is the base)
        apiUrl = "https://coreapi.visiontrack.xyz"  # Replace with your actual API URL
        
        # Create a list of image URLs
        image_urls = [f"{apiUrl}/{os.path.join('images', cameraId, img)}" for img in image_files]

        return {"status": "success", "images": image_urls}
    
    except Exception as e:
        return {"status": "error", "message": f"An error occurred: {str(e)}", "code": 500}

@app.get('/')
def read_status():
    return {"message": "I am working fine, don't worry!"}


