python validation.py -p "C:\Users\sanso\Documents\Uni\4t\TFG\other_datasets\discursoRey\wavs" "C:\Users\sanso\Desktop\ValidacionesTFG\discursoRey" --mode all > validations/discursoRey_realnormal_vs_fakenormal.txt

python validation.py -p "C:\Users\sanso\Documents\Uni\4t\TFG\other_datasets\discursoRey\wavs" "C:\Users\sanso\Desktop\ValidacionesTFG\discursoRey_enhanced" --mode all > validations/discursoRey_realnormal_vs_fakeenhanced.txt

python validation.py -p "C:\Users\sanso\Documents\Uni\4t\TFG\other_datasets\discursoRey_enhanced\wavs" "C:\Users\sanso\Desktop\ValidacionesTFG\discursoRey_enhanced" --mode all > validations/discursoRey_realenhanced_vs_fakeenhanced.txt

python validation.py -p "C:\Users\sanso\Documents\Uni\4t\TFG\other_datasets\MartaPeirano\wavs" "C:\Users\sanso\Desktop\ValidacionesTFG\MartaPeirano_FEMALE" --mode all > validations/MartaPeirano_FEMALE.txt

python validation.py -p "C:\Users\sanso\Documents\Uni\4t\TFG\other_datasets\MartaPeirano\wavs" "C:\Users\sanso\Desktop\ValidacionesTFG\MartaPeirano_MALE" --mode all > validations/MartaPeirano_MALE.txt

python validation.py -p "C:\Users\sanso\Documents\Uni\4t\TFG\sanso_old\wavs" "C:\Users\sanso\Desktop\ValidacionesTFG\sanso_old" --mode all > validations/sanso_old_vs_old.txt

python validation.py -p "C:\Users\sanso\Documents\Uni\4t\TFG\sanso_dataset\sanso_joined\wavs" "C:\Users\sanso\Desktop\ValidacionesTFG\sanso_old" --mode all > validations/sanso_realjoined_vs_fakeold.txt

python validation.py -p "C:\Users\sanso\Documents\Uni\4t\TFG\sanso_dataset\sanso_joined\wavs" "C:\Users\sanso\Desktop\ValidacionesTFG\sanso_joined" --mode all > validations/sanso_realjoined_vs_fakejoined.txt

python validation.py -p "C:\Users\sanso\Documents\Uni\4t\TFG\other_datasets\sansoEnhanced\wavs" "C:\Users\sanso\Desktop\ValidacionesTFG\sanso_joined" --mode all > validations/sanso_realjoined_vs_enhanced.txt

python validation.py -p "C:\Users\sanso\Documents\Uni\4t\TFG\other_datasets\sansoEnhanced\wavs" "C:\Users\sanso\Desktop\ValidacionesTFG\sanso_joined_enhanced" --mode all > validations/sanso_realenhanced_vs_enhanced.txt