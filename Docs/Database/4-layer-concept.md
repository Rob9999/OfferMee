# Refactoring into a Four-Layer Architecture

## Layered Architecture Overview

This document explains the implementation of a four-layer architecture, which separates responsibilities into distinct layers to ensure scalability, maintainability, and clarity.

```
┌──────────────────────────┐
│   1) Presentation/Views  │
└────────────┬─────────────┘
             │ (dict, JSON)
┌────────────▼─────────────┐
│   2) Application/Facade  │  <-- NEW: Business-Fassade
└────────────┬─────────────┘
             │ (Domain-Objekte, Dicts)
┌────────────▼─────────────┐
│   3) Services / Repos    │  <-- NEW: Business Services
└────────────┬─────────────┘
             │ (SQLAlchemy Models)
┌────────────▼─────────────┐
│   4) Data (DB / Models)  │
└──────────────────────────┘
```

### 1. Presentation / Views
The **Presentation/Views** layer is responsible for interacting with the user. It includes:
- Rendering UI components (e.g., Streamlit pages).
- Collecting user input.
- Displaying processed data returned from the Application layer.

Example:
```python
import streamlit as st
from application.facade import ExampleFacade

def render_page_example():
    st.header("Example Page")
    user_input = st.text_input("Enter your data:")

    if st.button("Submit"):
        result = ExampleFacade.process_data(user_input)
        st.success(f"Result: {result}")
```

### 2. Application / Facade
The **Application/Facade** layer acts as an intermediary between the Presentation layer and the underlying business logic or services. It ensures that the Presentation layer has no direct access to business rules or data handling logic.

Responsibilities:
- Exposing high-level operations to the Presentation layer.
- Coordinating between Services and Views.

Example:
```python
class ExampleFacade:
    @staticmethod
    def process_data(input_data):
        # Call the service layer to process the data
        from services.example_service import ExampleService
        return ExampleService.perform_processing(input_data)
```

### 3. Services / Repositories
The **Services/Repositories** layer contains the core business logic and interacts with the data layer. It is responsible for:
- Enforcing business rules.
- Coordinating data access and manipulation.

Example:
```python
class ExampleService:
    @staticmethod
    def perform_processing(data):
        # Business logic applied to data
        cleaned_data = data.strip().upper()
        # Interact with the repository to save or retrieve data
        from data.repositories.example_repo import ExampleRepository
        ExampleRepository.save(cleaned_data)
        return cleaned_data
```

### 4. Data (DB / Models)
The **Data** layer interacts with the database and provides an interface to perform CRUD operations. It uses SQLAlchemy models to map database tables.

Responsibilities:
- Mapping business objects to database tables.
- Performing raw queries or simple CRUD operations.

Example:
```python
from sqlalchemy import Column, String, Integer, create_engine, declarative_base

Base = declarative_base()

class ExampleModel(Base):
    __tablename__ = 'example'
    id = Column(Integer, primary_key=True)
    data = Column(String, nullable=False)

class ExampleRepository:
    @staticmethod
    def save(data):
        # Example for saving data using SQLAlchemy
        from sqlalchemy.orm import sessionmaker
        engine = create_engine('sqlite:///example.db')
        Session = sessionmaker(bind=engine)
        session = Session()

        new_entry = ExampleModel(data=data)
        session.add(new_entry)
        session.commit()
        session.close()
```

---

## Benefits of the Four-Layer Architecture
- **Scalability**: Each layer can be extended or replaced independently.
- **Maintainability**: Clear separation of concerns reduces the complexity of debugging and adding new features.
- **Reusability**: Business logic and data access are encapsulated, making them reusable across multiple presentations or applications.

---

This structure ensures clean code practices and facilitates future growth of the application.
