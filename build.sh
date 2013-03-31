cd installer
echo "Copying needed files for SFX..."
mkdir src/
cp ../script/daemon.py src/
echo "Creating SFX..."
tar -czf - * | pysfx -as "python install.py" - ../pylsa_sfx.py
echo "Removing copied files..."
rm -rf src
cd ..
