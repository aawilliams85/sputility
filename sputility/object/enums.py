from enum import IntEnum

class AaDataType(IntEnum):
    Undefined = -1
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
    ArrayReferenceType = 72
    ArrayStatusType = 73
    ArrayDataTypeType = 74

class AaExtension(IntEnum):
    Undefined = -1
    UserDefinedExtension = 586  # 4A 02 00 00
    ScriptExtension = 612       # 64 02 00 00
    InputExtension = 615        # 67 02 00 00
    HistoryExtension = 618      # 6A 02 00 00

class AaLocked(IntEnum):
    Undefined = -1
    Unlocked = 0
    Locked = 1
    InheritedLock = 2

class AaPermission(IntEnum):
    Undefined = -1
    FreeAccess = 0
    Operate = 1
    SecuredWrite = 2
    VerifiedWrite = 3
    Tune = 4
    Configure = 5
    ViewOnly = 6

class AaSource(IntEnum):
    Undefined = -1
    BuiltIn = 0
    Inherited = 1
    UserDefined = 2
    UserExtended = 3

class AaWriteability(IntEnum):
    Undefined = -1
    Calculated = 2
    CalculatedRetentive = 3
    ObjectWriteable = 5
    UserWriteable = 10
    ConfigOnly = 11
