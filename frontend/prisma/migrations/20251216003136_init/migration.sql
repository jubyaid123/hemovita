-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "name" TEXT,
    "email" TEXT NOT NULL,
    "passwordHash" TEXT NOT NULL,
    "age" INTEGER,
    "sex" TEXT,
    "country" TEXT,
    "pregnant" BOOLEAN,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "LabEntry" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "Hemoglobin" DOUBLE PRECISION,
    "MCV" DOUBLE PRECISION,
    "ferritin" DOUBLE PRECISION,
    "vitamin_B12" DOUBLE PRECISION,
    "folate_plasma" DOUBLE PRECISION,
    "vitamin_D" DOUBLE PRECISION,
    "magnesium" DOUBLE PRECISION,
    "zinc" DOUBLE PRECISION,
    "calcium" DOUBLE PRECISION,
    "vitamin_C" DOUBLE PRECISION,
    "vitamin_A" DOUBLE PRECISION,
    "vitamin_E" DOUBLE PRECISION,
    "vitamin_B6" DOUBLE PRECISION,
    "homocysteine" DOUBLE PRECISION,

    CONSTRAINT "LabEntry_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- AddForeignKey
ALTER TABLE "LabEntry" ADD CONSTRAINT "LabEntry_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
