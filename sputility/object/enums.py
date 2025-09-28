from enum import IntEnum

class AaDataType(IntEnum):
    NoneType = 0
    BooleanType = 1
    IntegerType = 2
    FloatType = 3
    DoubleType = 4
    StringType = 5
    TimeType = 6
    ElapsedTimeType = 7
    ReferenceType = 8
    StatusType = 9
    DataTypeType = 10
    SecurityClassificationType = 11
    DataQualityType = 12
    QualifiedEnumType = 13
    QualifiedStructType = 14
    InternationalizedStringType = 15
    BigStringType = 16
    ArrayBooleanType = 65
    ArrayIntegerType = 66
    ArrayFloatType = 67
    ArrayDoubleType = 68
    ArrayStringType = 69
    ArrayTimeType = 70
    ArrayElapsedTimeType = 71

class AaPermission(IntEnum):
    FreeAccess = 0
    Operate = 1
    SecuredWrite = 2
    VerifiedWrite = 3
    Tune = 4
    Configure = 5
    ViewOnly = 6

class AaWriteability(IntEnum):
    Calculated = 2
    CalculatedRetentive = 3
    ObjectWriteable = 5
    UserWriteable = 10
    ConfigOnly = 11
