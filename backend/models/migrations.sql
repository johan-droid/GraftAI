-- SQL Server migration template for initial schema
-- Users table
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[users] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        full_name VARCHAR(255) NULL,
        is_active BIT NOT NULL DEFAULT 1,
        is_superuser BIT NOT NULL DEFAULT 0,
        hashed_password VARCHAR(512) NULL,
        timezone VARCHAR(100) NOT NULL DEFAULT 'UTC',
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE UNIQUE INDEX UX_Users_Email ON [dbo].[users](email);
END

-- Organizations table
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[organizations]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[organizations] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        owner_id INT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_Organizations_Owner FOREIGN KEY (owner_id) REFERENCES [dbo].[users](id)
    );
END

-- Bookings table
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[bookings]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[bookings] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        organization_id INT NULL,
        start_time DATETIME2 NOT NULL,
        end_time DATETIME2 NOT NULL,
        status VARCHAR(50) NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_Bookings_User FOREIGN KEY (user_id) REFERENCES [dbo].[users](id),
        CONSTRAINT FK_Bookings_Organization FOREIGN KEY (organization_id) REFERENCES [dbo].[organizations](id)
    );
END

-- Auth sessions table
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[auth_sessions]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[auth_sessions] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        session_token VARCHAR(255) NOT NULL,
        expires_at DATETIME2 NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_AuthSessions_User FOREIGN KEY (user_id) REFERENCES [dbo].[users](id)
    );
END

-- Audit logs table
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[audit_logs]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[audit_logs] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        action VARCHAR(255) NOT NULL,
        ip_address VARCHAR(64) NULL,
        user_agent VARCHAR(255) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_AuditLogs_User FOREIGN KEY (user_id) REFERENCES [dbo].[users](id)
    );
END

-- Preferences table
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[preferences]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[preferences] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        [key] VARCHAR(255) NOT NULL,
        [value] NVARCHAR(MAX) NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_Preferences_User FOREIGN KEY (user_id) REFERENCES [dbo].[users](id)
    );
END
