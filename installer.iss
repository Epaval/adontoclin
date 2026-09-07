[Setup]
AppName=OdontoClin
AppVersion=0.1.0
AppPublisher=Tu Laboratorio Software
DefaultDirName={autopf}\LabClinico
DefaultGroupName=Lab Clínico
OutputDir=instalador
OutputBaseFilename=OdontoClin-Setup-0.1.0
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear ícono en el escritorio"
Name: "autoiniciar"; Description: "Iniciar servidor al encender Windows"; GroupDescription: "Servidor:"; Flags: unchecked; Check: IsServidor

[Files]
Source: "dist\LabClinico\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icons\*.ico"; DestDir: "{app}\icons"; Flags: ignoreversion

[Icons]
Name: "{group}\Lab Clínico"; Filename: "{app}\LabClinico.exe"; IconFilename: "{app}\icons\icono_principal.ico"; Check: NotIsEstacion
Name: "{group}\Lab Clínico Servidor (red)"; Filename: "{app}\LabClinico.exe"; Parameters: "--lan --sin-ventana"; IconFilename: "{app}\icons\icono_servidor.ico"; Check: IsServidor
Name: "{group}\Lab Clínico Estación"; Filename: "{app}\LabClinico.exe"; Parameters: "--conectar"; IconFilename: "{app}\icons\icono_estacion.ico"; Check: IsEstacion

Name: "{autodesktop}\Lab Clínico"; Filename: "{app}\LabClinico.exe"; Tasks: desktopicon; IconFilename: "{app}\icons\icono_principal.ico"; Check: NotIsEstacion
Name: "{autodesktop}\Lab Clínico Servidor"; Filename: "{app}\LabClinico.exe"; Parameters: "--lan --sin-ventana"; Tasks: desktopicon; IconFilename: "{app}\icons\icono_servidor.ico"; Check: IsServidor
Name: "{autodesktop}\Lab Clínico Estación"; Filename: "{app}\LabClinico.exe"; Parameters: "--conectar"; Tasks: desktopicon; IconFilename: "{app}\icons\icono_estacion.ico"; Check: IsEstacion

Name: "{userstartup}\Lab Clínico Servidor"; Filename: "{app}\LabClinico.exe"; Parameters: "--lan --sin-ventana"; Tasks: autoiniciar; IconFilename: "{app}\icons\icono_servidor.ico"; Check: IsServidor

[Run]
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""Lab Clinico"" dir=in action=allow program=""{app}\LabClinico.exe"" enable=yes"; Flags: runhidden; Check: IsServidor
Filename: "{app}\LabClinico.exe"; Parameters: "--conectar"; Description: "Abrir Lab Clínico Estación ahora"; Flags: nowait postinstall skipifsilent; Check: IsEstacion
Filename: "{app}\LabClinico.exe"; Description: "Abrir Lab Clínico ahora"; Flags: nowait postinstall skipifsilent; Check: NotIsEstacion

[Code]
var
  RolPage: TInputOptionWizardPage;
  IpPage: TInputQueryWizardPage;
  RolSeleccionado: String;

procedure InitializeWizard();
begin
  RolPage := CreateInputOptionPage(wpSelectDir,
    'Tipo de instalación', '¿Cómo se usará esta PC?',
    'Seleccione el rol de esta computadora en el laboratorio:',
    True, False);
  RolPage.Add('Servidor (PC principal): hospedará la base de datos del laboratorio.');
  RolPage.Add('Estación de trabajo: se conectará al servidor para trabajar en red.');
  RolPage.Add('Instalación individual: uso en esta PC sin conexión en red.');
  RolPage.Values[0] := True;

  IpPage := CreateInputQueryPage(RolPage.ID,
    'Conexión con el servidor', 'Dirección IP del servidor',
    'Ingrese la IP de la PC donde está (o estará) instalado el servidor.');
  IpPage.Add('IP del servidor:', False);
  IpPage.Values[0] := '';
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if PageID = IpPage.ID then
    Result := (RolSeleccionado <> 'estacion');
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  if CurPageID = RolPage.ID then
  begin
    if RolPage.Values[0] then
      RolSeleccionado := 'servidor'
    else if RolPage.Values[1] then
      RolSeleccionado := 'estacion'
    else
      RolSeleccionado := 'individual';
  end;

  if CurPageID = IpPage.ID then
  begin
    if Trim(IpPage.Values[0]) = '' then
    begin
      MsgBox('Debe ingresar la IP del servidor para continuar.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function IsServidor: Boolean;
begin
  Result := (RolSeleccionado = 'servidor');
end;

function IsEstacion: Boolean;
begin
  Result := (RolSeleccionado = 'estacion');
end;

function NotIsEstacion: Boolean;
begin
  Result := (RolSeleccionado <> 'estacion');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    SaveStringToFile(ExpandConstant('{app}\rol.txt'), RolSeleccionado, False);
    if RolSeleccionado = 'estacion' then
      SaveStringToFile(ExpandConstant('{app}\ip_servidor.txt'), Trim(IpPage.Values[0]), False);
  end;
end;
