// Limites das colunas no PostgreSQL: valores acima disso estourariam no banco (erro 500)
const MAX_INT = 2147483647; // INTEGER
const MAX_PRECO = 99999999.99; // NUMERIC(10,2)

function inteiroPositivo(valor) {
  return Number.isInteger(valor) && valor > 0 && valor <= MAX_INT;
}

function inteiroNaoNegativo(valor) {
  return Number.isInteger(valor) && valor >= 0 && valor <= MAX_INT;
}

module.exports = { MAX_INT, MAX_PRECO, inteiroPositivo, inteiroNaoNegativo };
