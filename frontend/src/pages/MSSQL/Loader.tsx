import { useState } from "react";
import { Download, Upload, CheckCircle, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { FileUploader } from "../../components/Loader/FileUploader";
import { Progress } from "../../components/ui/progress";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { parseFile, generateSampleTemplate } from "../../utils/csvHelpers";
import { toast } from "sonner";
import api from "../../services/api";

interface ValidationError {
  row: number;
  error: string;
}

interface UploadStatus {
  status: "idle" | "validating" | "uploading" | "complete" | "error";
  message?: string;
  progress: number;
}

const MSSQLLoader = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
    status: "idle",
    progress: 0
  });
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [fileInfo, setFileInfo] = useState<{
    name: string;
    size: string;
    rows?: number;
  } | null>(null);

  const handleFileAccepted = async (uploadedFile: File) => {
    try {
      setFile(uploadedFile);
      
      // Parsear solo para mostrar info, no para enviar datos
      const data = await parseFile(uploadedFile);
      
      setFileInfo({
        name: uploadedFile.name,
        size: `${(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB`,
        rows: data.rows.length
      });
      
      toast.success(`File ready: ${data.rows.length} rows found`);
    } catch (error) {
      toast.error("Failed to parse file");
      console.error(error);
    }
  };

  const handleDryRun = async () => {
    if (!file) return;
    
    setUploadStatus({ status: "validating", progress: 0 });
    setValidationErrors([]);
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const response = await api.post("/mssql/loader/validate-file", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = (progressEvent.loaded / progressEvent.total) * 100;
            setUploadStatus(prev => ({ ...prev, progress }));
          }
        },
      });
      
      if (response.data.errors && response.data.errors.length > 0) {
        setValidationErrors(response.data.errors);
        toast.warning(`Validation found ${response.data.errors.length} errors`);
      } else {
        toast.success("File validated successfully!");
      }
    } catch (error: any) {
      console.error("Validation error:", error);
      toast.error(error.response?.data?.message || "Validation failed");
    } finally {
      setUploadStatus({ status: "idle", progress: 0 });
    }
  };

  const handleChunkedUpload = async () => {
    if (!file) return;
    
    const CHUNK_SIZE = 1024 * 1024; // 1MB chunks
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    
    setUploadStatus({ 
      status: "uploading", 
      progress: 0,
      message: `Preparing to upload ${totalChunks} chunks...`
    });

    try {
      // Primero iniciar la sesión de upload
      const initResponse = await api.post("/mssql/loader/init-upload", {
        fileName: file.name,
        fileSize: file.size,
        totalChunks: totalChunks,
        fileType: file.type
      });

      const uploadId = initResponse.data.uploadId;

      // Subir cada chunk
      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        const start = chunkIndex * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);
        
        const formData = new FormData();
        formData.append("file", chunk);
        formData.append("uploadId", uploadId);
        formData.append("chunkIndex", chunkIndex.toString());
        formData.append("totalChunks", totalChunks.toString());
        formData.append("fileName", file.name);
        formData.append("fileType", file.type);

        await api.post("/mssql/loader/upload-chunk", formData, {
          headers: { 
            "Content-Type": "multipart/form-data",
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const chunkProgress = (progressEvent.loaded / progressEvent.total) * (100 / totalChunks);
              const overallProgress = (chunkIndex / totalChunks) * 100 + chunkProgress;
              setUploadStatus(prev => ({
                ...prev,
                progress: overallProgress,
                message: `Uploading chunk ${chunkIndex + 1} of ${totalChunks}`
              }));
            }
          },
        });
      }

      // Finalizar el upload y procesar el archivo
      setUploadStatus({
        status: "uploading",
        progress: 95,
        message: "Processing file..."
      });

      const finalResponse = await api.post("/mssql/loader/complete-upload", {
        uploadId: uploadId
      });

      setUploadStatus({
        status: "complete",
        progress: 100,
        message: `Successfully imported ${finalResponse.data.importedRows} rows!`
      });

      toast.success(`Import completed! ${finalResponse.data.importedRows} rows imported.`);
      
    } catch (error: any) {
      console.error("Upload error:", error);
      setUploadStatus({
        status: "error",
        progress: 0,
        message: error.response?.data?.message || "Upload failed"
      });
      toast.error("Upload failed");
    }
  };

  const downloadTemplate = () => {
    generateSampleTemplate(
      [
        "ClienteEmail",
        "ClienteNombre",
        "SKU",
        "CodigoAlt",
        "Fecha",
        "Canal",
        "Moneda",
        "Qty",
        "PrecioUnit",
        "DescuentoPct",
        "MetadataJSON",
      ],
      "mssql_loader_template.csv"
    );
  };

  const resetUpload = () => {
    setFile(null);
    setFileInfo(null);
    setValidationErrors([]);
    setUploadStatus({ status: "idle", progress: 0 });
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-mssql">MS SQL Bulk Loader</h1>
        <p className="text-muted-foreground mt-1">Import sales data from CSV/Excel files</p>
      </div>

      <div className="grid gap-6">
        <Card className="border-l-4 border-mssql">
          <CardHeader>
            <CardTitle>Step 1: Download Template</CardTitle>
            <CardDescription>Get the CSV template with correct column headers</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={downloadTemplate}>
              <Download className="h-4 w-4 mr-2" />
              Download Sample Template
            </Button>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-mssql">
          <CardHeader>
            <CardTitle>Step 2: Upload File</CardTitle>
            <CardDescription>Upload your CSV or Excel file</CardDescription>
          </CardHeader>
          <CardContent>
            {!file ? (
              <FileUploader onFileAccepted={handleFileAccepted} />
            ) : (
              <div className="space-y-4">
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    File loaded: {fileInfo?.name} • {fileInfo?.rows || '?'} rows • {fileInfo?.size}
                  </AlertDescription>
                </Alert>
                
                <div className="flex gap-2 flex-wrap">
                  <Button variant="outline" onClick={resetUpload}>
                    Clear File
                  </Button>
                  <Button
                    className="bg-yellow-600 hover:bg-yellow-700"
                    onClick={handleDryRun}
                    disabled={uploadStatus.status === "validating" || uploadStatus.status === "uploading"}
                  >
                    {uploadStatus.status === "validating" ? "Validating..." : "Dry Run (Validate)"}
                  </Button>
                  <Button
                    className="bg-mssql hover:bg-mssql-dark"
                    onClick={handleChunkedUpload}
                    disabled={uploadStatus.status === "uploading" || uploadStatus.status === "validating" || validationErrors.length > 0}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Start Import
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Progress Indicator */}
        {(uploadStatus.status === "validating" || uploadStatus.status === "uploading") && (
          <Card className="border-l-4 border-blue-500">
            <CardHeader>
              <CardTitle>
                {uploadStatus.status === "validating" ? "Validating File..." : "Uploading File..."}
              </CardTitle>
              <CardDescription>{uploadStatus.message}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Progress value={uploadStatus.progress} />
              <p className="text-sm text-muted-foreground text-center">
                {Math.round(uploadStatus.progress)}% • {uploadStatus.message}
              </p>
            </CardContent>
          </Card>
        )}

        {validationErrors.length > 0 && (
          <Card className="border-l-4 border-destructive">
            <CardHeader>
              <CardTitle className="text-destructive">Validation Errors</CardTitle>
              <CardDescription>{validationErrors.length} rows have errors</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {validationErrors.slice(0, 10).map((error, idx) => (
                  <Alert key={idx} variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Row {error.row}: {error.error}
                    </AlertDescription>
                  </Alert>
                ))}
                {validationErrors.length > 10 && (
                  <p className="text-sm text-muted-foreground">
                    + {validationErrors.length - 10} more errors
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {uploadStatus.status === "complete" && (
          <Alert className="bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-600">
              {uploadStatus.message}
            </AlertDescription>
          </Alert>
        )}

        {uploadStatus.status === "error" && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {uploadStatus.message}
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
};

export default MSSQLLoader;