instructions = [
    "USE SARV3"

    """
    DROP TABLE IF EXISTS Users
    DROP TABLE IF EXISTS Validators
    DROP TABLE IF EXISTS Resources
    DROP TABLE IF EXISTS Requests
    DROP TABLE IF EXISTS Permissions
    
    CREATE TABLE [dbo].[Users](
        [username] [nchar](10) NOT NULL,
        [mail] [nvarchar](50) NULL,
        [name] [nvarchar](50) NULL,
        [isAdmin] [bit] NULL,
        [isValidator] [bit] NULL,
    CONSTRAINT [PK_Users] PRIMARY KEY CLUSTERED 
    (
        [username] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]

    CREATE TABLE Validators (
        [resource] [nvarchar](50) NOT NULL,
	    [username] [nchar](10) NOT NULL
    )

    CREATE TABLE Resources (
        [name] [nvarchar](50) NOT NULL,
        [description] [nvarchar](250) NULL,
        [owner] [nchar](10) NOT NULL,
        [path] [nvarchar](250) NULL,
        [ADGroup] [nvarchar](50) NULL,
        CONSTRAINT [PK_Resources] PRIMARY KEY CLUSTERED 
(
	[name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
    

    CREATE TABLE Requests (
        [resource] [nvarchar](50) NOT NULL,
        [username] [nchar](10) NOT NULL,
        [validator] [nchar](10) NOT NULL,
        [UID] [uniqueidentifier] NOT NULL,
        [status] [nchar](10) NULL,
        [date] [datetime2] NOT NULL
    )

    CREATE TABLE Permissions (
        [resouce] [nvarchar](50) NOT NULL,
        [username] [nchar](10) NOT NULL,
        [date] [datetime2] NOT NULL
    )

    CREATE TABLE [dbo].[Profiles](
	[name] [nchar](50) NOT NULL,
	[groups] [nvarchar](max) NOT NULL
    """

]