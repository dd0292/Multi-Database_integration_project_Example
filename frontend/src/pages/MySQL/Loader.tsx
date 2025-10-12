import { useState } from "react";
import { Download, Upload, CheckCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { FileUploader } from "../../components/Loader/FileUploader";
import { Progress } from "../../components/ui/progress";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { parseFile, generateSampleTemplate } from "../../utils/csvHelpers";
import { toast } from "sonner";
import api from "../../services/api";

const MySQLLoader = () => {
  const [file, setFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<any>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "complete">("idle");

  const handleFileAccepted = async (uploadedFile: File) => {
    try {
      setFile(uploadedFile);
      const data = await parseFile(uploadedFile);
      setParsedData(data);
      toast.success(`File parsed: ${data.rows.length} rows found`);
    } catch (error) {
      toast.error("Failed to parse file");
    }
  };

  const handleUpload = async () => {
    if (!parsedData) return;
    
    setUploadStatus("uploading");
    setUploadProgress(0);
    
    const chunkSize = 500;
    const chunks = [];
    
    for (let i = 0; i < parsedData.rows.length; i += chunkSize) {
      chunks.push(parsedData.rows.slice(i, i + chunkSize));
    }
    
    try {
      for (let i = 0; i < chunks.length; i++) {
        await api.post("/mysql/loader/upload", {
          rows: chunks[i],
        });
        setUploadProgress(((i + 1) / chunks.length) * 100);
      }
      
      setUploadStatus("complete");
      toast.success(`Successfully imported ${parsedData.rows.length} rows!`);
    } catch (error) {
      setUploadStatus("idle");
      toast.error("Upload failed");
    }
  };

  const downloadTemplate = () => {
    generateSampleTemplate(
      [
        "cliente_email",
        "producto_codigo_alt",
        "fecha",
        "canal",
        "moneda",
        "total",
        "precio_unit",
        "cantidad",
        "metadata",
      ],
      "mysql_loader_template.csv"
    );
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-mysql">MySQL Bulk Loader</h1>
        <p className="text-muted-foreground mt-1">Import sales data from CSV/Excel files</p>
      </div>

      <div className="grid gap-6">
        <Card className="border-l-4 border-mysql">
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

        <Card className="border-l-4 border-mysql">
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
                    File loaded: {file.name} • {parsedData?.rows.length || 0} rows
                  </AlertDescription>
                </Alert>
                <Button variant="outline" onClick={() => setFile(null)}>
                  Clear File
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {parsedData && uploadStatus !== "complete" && (
          <Card className="border-l-4 border-mysql">
            <CardHeader>
              <CardTitle>Step 3: Import Data</CardTitle>
              <CardDescription>Upload rows to database</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {uploadStatus === "uploading" && (
                <div className="space-y-2">
                  <Progress value={uploadProgress} />
                  <p className="text-sm text-muted-foreground text-center">
                    Uploading... {Math.round(uploadProgress)}%
                  </p>
                </div>
              )}
              <Button
                className="bg-mysql hover:bg-mysql-dark"
                onClick={handleUpload}
                disabled={uploadStatus === "uploading"}
              >
                <Upload className="h-4 w-4 mr-2" />
                Start Import
              </Button>
            </CardContent>
          </Card>
        )}

        {uploadStatus === "complete" && (
          <Alert>
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-600">
              Import completed! {parsedData?.rows.length} rows imported.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
};

export default MySQLLoader;
