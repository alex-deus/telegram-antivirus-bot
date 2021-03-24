lint:
	@pre-commit run --all-files

update-isort:
	@seed-isort-config
	@echo "[+] Is done"
