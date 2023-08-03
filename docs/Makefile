#
# Makefile
# Development by Carl J. Nobile
#

FQDN		= $(shell hostname --fqdn)
DOC_DIR		= $(shell pwd)
SRC_DIR		= ${DOC_DIR}../src
URL		= http://${FQDN}${DOC_DIR}/${API_DIR}/index.html
TARBALL_NAME	= noncom-financial

all	: api-docs

#----------------------------------------------------------------------
.PHONY	: app-docs
app-docs:
	@(cd ..; epydoc -v --docformat epytext \
          --name "Noncommercial Financial" -o docs/api --show-private \
          --show-imports --graph all --url "${URL}" ${SRC_DIR}/*.py \
         )
#----------------------------------------------------------------------
tar	:
	@(ln -s ${API_DIR} ${TARBALL_NAME}; \
          tar -chzvf ${TARBALL_NAME}.tar.gz ${TARBALL_NAME})
#----------------------------------------------------------------------

clean	:
	@rm -f *~ \#* .\#*

clobber	: clean
	@rm -rf ${TARBALL_NAME} ${TARBALL_NAME}.tar.gz 
